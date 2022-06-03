# Copyright (C) 2018 The Electrum developers
# Distributed under the MIT software license, see the accompanying
# file LICENCE or http://www.opensource.org/licenses/mit-license.php

import os
import json
import sys
import threading
import traceback
from typing import Tuple, List, Callable, NamedTuple, Optional, TYPE_CHECKING
from functools import partial

from PyQt5.QtCore import QRect, QEventLoop, Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QPen, QPainter, QPixmap
from PyQt5.QtWidgets import (QWidget, QDialog, QLabel, QHBoxLayout, QMessageBox,
                             QVBoxLayout, QLineEdit, QFileDialog, QPushButton,
                             QGridLayout, QSlider, QScrollArea, QApplication)

from electrum.wallet import Wallet, Abstract_Wallet
from electrum.storage import WalletStorage, StorageReadWriteError
from electrum.util import UserCancelled, InvalidPassword, WalletFileException, get_new_wallet_name
from electrum.base_wizard import BaseWizard, HWD_SETUP_DECRYPT_WALLET, GoBack, ReRunDialog
from electrum.network import Network
from electrum.i18n import _

from .seed_dialog import SeedLayout, KeysLayout
from .network_dialog import NetworkChoiceLayout
from .util import (MessageBoxMixin, Buttons, icon_path, ChoicesLayout, WWLabel,
                   InfoButton, char_width_in_lineedit, PasswordLineEdit)
from .password_dialog import PasswordLayout, PasswordLayoutForHW, PW_NEW
from .bip39_recovery_dialog import Bip39RecoveryDialog
from electrum.plugin import run_hook, Plugins

if TYPE_CHECKING:
    from electrum.simple_config import SimpleConfig
    from electrum.wallet_db import WalletDB
    from . import ElectrumGui


MSG_ENTER_PASSWORD = _("Choose a password to encrypt your wallet keys.") + '\n'\
                     + _("Leave this field empty if you want to disable encryption.")
MSG_HW_STORAGE_ENCRYPTION = _("Set wallet file encryption.") + '\n'\
                          + _("Your wallet file does not contain secrets, mostly just metadata. ") \
                          + _("It also contains your master public key that allows watching your addresses.") + '\n\n'\
                          + _("Note: If you enable this setting, you will need your hardware device to open your wallet.")
WIF_HELP_TEXT = (_('WIF keys are typed in Electrum, based on script type.') + '\n\n' +
                 _('A few examples') + ':\n' +
                 'p2pkh:KxZcY47uGp9a...       \t-> 1DckmggQM...\n' +
                 'p2wpkh-p2sh:KxZcY47uGp9a... \t-> 3NhNeZQXF...\n' +
                 'p2wpkh:KxZcY47uGp9a...      \t-> bc1q3fjfk...')
# note: full key is KxZcY47uGp9aVQAb6VVvuBs8SwHKgkSR2DbZUzjDzXf2N2GPhG9n
MSG_PASSPHRASE_WARN_ISSUE4566 = _("Warning") + ": "\
                              + _("You have multiple consecutive whitespaces or leading/trailing "
                                  "whitespaces in your passphrase.") + " " \
                              + _("This is discouraged.") + " " \
                              + _("Due to a bug, old versions of Electrum will NOT be creating the "
                                  "same wallet as newer versions or other software.")


class CosignWidget(QWidget):
    size = 120

    def __init__(self, m, n):
        QWidget.__init__(self)
        self.R = QRect(0, 0, self.size, self.size)
        self.setGeometry(self.R)
        self.setMinimumHeight(self.size)
        self.setMaximumHeight(self.size)
        self.m = m
        self.n = n

    def set_n(self, n):
        self.n = n
        self.update()

    def set_m(self, m):
        self.m = m
        self.update()

    def paintEvent(self, event):
        bgcolor = self.palette().color(QPalette.Background)
        pen = QPen(bgcolor, 7, Qt.SolidLine)
        qp = QPainter()
        qp.begin(self)
        qp.setPen(pen)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setBrush(Qt.gray)
        for i in range(self.n):
            alpha = int(16* 360 * i/self.n)
            alpha2 = int(16* 360 * 1/self.n)
            qp.setBrush(Qt.green if i<self.m else Qt.gray)
            qp.drawPie(self.R, alpha, alpha2)
        qp.end()



def wizard_dialog(func):
    def func_wrapper(*args, **kwargs):
        run_next = kwargs['run_next']
        wizard = args[0]  # type: InstallWizard
        while True:
            #wizard.logger.debug(f"dialog stack. len: {len(wizard._stack)}. stack: {wizard._stack}")
            wizard.back_button.setText(_('Back') if wizard.can_go_back() else _('Cancel'))
            # current dialog
            try:
                out = func(*args, **kwargs)
                if type(out) is not tuple:
                    out = (out,)
            except GoBack:
                if not wizard.can_go_back():
                    wizard.close()
                    raise UserCancelled
                else:
                    # to go back from the current dialog, we just let the caller unroll the stack:
                    raise
            # next dialog
            try:
                while True:
                    try:
                        run_next(*out)
                    except ReRunDialog:
                        # restore state, and then let the loop re-run next
                        wizard.go_back(rerun_previous=False)
                    else:
                        break
            except GoBack as e:
                # to go back from the next dialog, we ask the wizard to restore state
                wizard.go_back(rerun_previous=False)
                # and we re-run the current dialog
                if wizard.can_go_back():
                    # also rerun any calculations that might have populated the inputs to the current dialog,
                    # by going back to just after the *previous* dialog finished
                    raise ReRunDialog() from e
                else:
                    continue
            else:
                break
    return func_wrapper


class WalletAlreadyOpenInMemory(Exception):
    def __init__(self, wallet: Abstract_Wallet):
        super().__init__()
        self.wallet = wallet


# WindowModalDialog must come first as it overrides show_error
class InstallWizard(QDialog, MessageBoxMixin, BaseWizard):

    accept_signal = pyqtSignal()

    def __init__(self, config: 'SimpleConfig', app: QApplication, plugins: 'Plugins', *, gui_object: 'ElectrumGui'):
        QDialog.__init__(self, None)
        BaseWizard.__init__(self, config, plugins)
        self.setWindowTitle('Electrum  -  ' + _('Install Wizard'))
        self.app = app
        self.config = config
        self.gui_thread = gui_object.gui_thread
        self.setMinimumSize(600, 400)
        self.accept_signal.connect(self.accept)
        self.title = QLabel()
        self.main_widget = QWidget()
        self.back_button = QPushButton(_("Back"), self)
        self.back_button.setText(_('Back') if self.can_go_back() else _('Cancel'))
        self.next_button = QPushButton(_("Next"), self)
        self.next_button.setDefault(True)
        self.logo = QLabel()
        self.please_wait = QLabel(_("Please wait..."))
        self.please_wait.setAlignment(Qt.AlignCenter)
        self.icon_filename = None
        self.loop = QEventLoop()
        self.rejected.connect(lambda: self.loop.exit(0))
        self.back_button.clicked.connect(lambda: self.loop.exit(1))
        self.next_button.clicked.connect(lambda: self.loop.exit(2))
        outer_vbox = QVBoxLayout(self)
        inner_vbox = QVBoxLayout()
        inner_vbox.addWidget(self.title)
        inner_vbox.addWidget(self.main_widget)
        inner_vbox.addStretch(1)
        inner_vbox.addWidget(self.please_wait)
        inner_vbox.addStretch(1)
        scroll_widget = QWidget()
        scroll_widget.setLayout(inner_vbox)
        scroll = QScrollArea()
        scroll.setFocusPolicy(Qt.NoFocus)
        scroll.setWidget(scroll_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        icon_vbox = QVBoxLayout()
        icon_vbox.addWidget(self.logo)
        icon_vbox.addStretch(1)
        hbox = QHBoxLayout()
        hbox.addLayout(icon_vbox)
        hbox.addSpacing(5)
        hbox.addWidget(scroll)
        hbox.setStretchFactor(scroll, 1)
        outer_vbox.addLayout(hbox)
        outer_vbox.addLayout(Buttons(self.back_button, self.next_button))
        self.set_icon('electrum.png')
        self.show()
        self.raise_()
        self.refresh_gui()  # Need for QT on MacOSX.  Lame.

    def select_storage(self, path, get_wallet_from_daemon) -> Tuple[str, Optional[WalletStorage]]:
        if os.path.isdir(path):
            raise Exception("wallet path cannot point to a directory")

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(_('Wallet') + ':'))
        name_e = QLineEdit()
        hbox.addWidget(name_e)
        button = QPushButton(_('Choose...'))
        hbox.addWidget(button)
        vbox.addLayout(hbox)

        msg_label = WWLabel('')
        vbox.addWidget(msg_label)
        hbox2 = QHBoxLayout()
        pw_e = PasswordLineEdit('', self)
        pw_e.setFixedWidth(17 * char_width_in_lineedit())
        pw_label = QLabel(_('Password') + ':')
        hbox2.addWidget(pw_label)
        hbox2.addWidget(pw_e)
        hbox2.addStretch()
        vbox.addLayout(hbox2)

        vbox.addSpacing(50)
        vbox_create_new = QVBoxLayout()
        vbox_create_new.addWidget(QLabel(_('Alternatively') + ':'), alignment=Qt.AlignLeft)
        button_create_new = QPushButton(_('Create New Wallet'))
        button_create_new.setMinimumWidth(120)
        vbox_create_new.addWidget(button_create_new, alignment=Qt.AlignLeft)
        widget_create_new = QWidget()
        widget_create_new.setLayout(vbox_create_new)
        vbox_create_new.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(widget_create_new)

        self.set_layout(vbox, title=_('Electrum wallet'))

        temp_storage = None  # type: Optional[WalletStorage]
        wallet_folder = os.path.dirname(path)

        def on_choose():
            path, __ = QFileDialog.getOpenFileName(self, "Select your wallet file", wallet_folder)
            if path:
                name_e.setText(path)

        def on_filename(filename):
            # FIXME? "filename" might contain ".." (etc) and hence sketchy path traversals are possible
            nonlocal temp_storage
            temp_storage = None
            msg = None
            if filename:
                path = os.path.join(wallet_folder, filename)
                wallet_from_memory = get_wallet_from_daemon(path)
                try:
                    if wallet_from_memory:
                        temp_storage = wallet_from_memory.storage  # type: Optional[WalletStorage]
                    else:
                        temp_storage = WalletStorage(path)
                except (StorageReadWriteError, WalletFileException) as e:
                    msg = _('Cannot read file') + f'\n{repr(e)}'
                except Exception as e:
                    self.logger.exception('')
                    msg = _('Cannot read file') + f'\n{repr(e)}'
            else:
                msg = ""
            self.next_button.setEnabled(temp_storage is not None)
            user_needs_to_enter_password = False
            if temp_storage:
                if not temp_storage.file_exists():
                    msg =_("This file does not exist.") + '\n' \
                          + _("Press 'Next' to create this wallet, or choose another file.")
                elif not wallet_from_memory:
                    if temp_storage.is_encrypted_with_user_pw():
                        msg = _("This file is encrypted with a password.") + '\n' \
                              + _('Enter your password or choose another file.')
                        user_needs_to_enter_password = True
                    elif temp_storage.is_encrypted_with_hw_device():
                        msg = _("This file is encrypted using a hardware device.") + '\n' \
                              + _("Press 'Next' to choose device to decrypt.")
                    else:
                        msg = _("Press 'Next' to open this wallet.")
                else:
                    msg = _("This file is already open in memory.") + "\n" \
                        + _("Press 'Next' to create/focus window.")
            if msg is None:
                msg = _('Cannot read file')
            msg_label.setText(msg)
            widget_create_new.setVisible(bool(temp_storage and temp_storage.file_exists()))
            if user_needs_to_enter_password:
                pw_label.show()
                pw_e.show()
                pw_e.setFocus()
            else:
                pw_label.hide()
                pw_e.hide()

        button.clicked.connect(on_choose)
        button_create_new.clicked.connect(
            lambda: name_e.setText(get_new_wallet_name(wallet_folder)))  # FIXME get_new_wallet_name might raise
        name_e.textChanged.connect(on_filename)
        name_e.setText(os.path.basename(path))

        def run_user_interaction_loop():
            while True:
                if self.loop.exec_() != 2:  # 2 = next
                    raise UserCancelled()
                assert temp_storage
                if temp_storage.file_exists() and not temp_storage.is_encrypted():
                    break
                if not temp_storage.file_exists():
                    break
                wallet_from_memory = get_wallet_from_daemon(temp_storage.path)
                if wallet_from_memory:
                    raise WalletAlreadyOpenInMemory(wallet_from_memory)
                if temp_storage.file_exists() and temp_storage.is_encrypted():
                    if temp_storage.is_encrypted_with_user_pw():
                        password = pw_e.text()
                        try:
                            temp_storage.decrypt(password)
                            break
                        except InvalidPassword as e:
                            self.show_message(title=_('Error'), msg=str(e))
                            continue
                        except BaseException as e:
                            self.logger.exception('')
                            self.show_message(title=_('Error'), msg=repr(e))
                            raise UserCancelled()
                    elif temp_storage.is_encrypted_with_hw_device():
                        try:
                            self.run('choose_hw_device', HWD_SETUP_DECRYPT_WALLET, storage=temp_storage)
                        except InvalidPassword as e:
                            self.show_message(title=_('Error'),
                                              msg=_('Failed to decrypt using this hardware device.') + '\n' +
                                                  _('If you use a passphrase, make sure it is correct.'))
                            self.reset_stack()
                            return self.select_storage(path, get_wallet_from_daemon)
                        except (UserCancelled, GoBack):
                            raise
                        except BaseException as e:
                            self.logger.exception('')
                            self.show_message(title=_('Error'), msg=repr(e))
                            raise UserCancelled()
                        if temp_storage.is_past_initial_decryption():
                            break
                        else:
                            raise UserCancelled()
                    else:
                        raise Exception('Unexpected encryption version')

        try:
            run_user_interaction_loop()
        finally:
            try:
                pw_e.clear()
            except RuntimeError:  # wrapped C/C++ object has been deleted.
                pass              # happens when decrypting with hw device

        return temp_storage.path, (temp_storage if temp_storage.file_exists() else None)

    def run_upgrades(self, storage: WalletStorage, db: 'WalletDB') -> None:
        path = storage.path
        if db.requires_split():
            self.hide()
            msg = _("The wallet '{}' contains multiple accounts, which are no longer supported since Electrum 2.7.\n\n"
                    "Do you want to split your wallet into multiple files?").format(path)
            if not self.question(msg):
                return
            file_list = db.split_accounts(path)
            msg = _('Your accounts have been moved to') + ':\n' + '\n'.join(file_list) + '\n\n'+ _('Do you want to delete the old file') + ':\n' + path
            if self.question(msg):
                os.remove(path)
                self.show_warning(_('The file was removed'))
            # raise now, to avoid having the old storage opened
            raise UserCancelled()

        action = db.get_action()
        if action and db.requires_upgrade():
            raise WalletFileException('Incomplete wallet files cannot be upgraded.')
        if action:
            self.hide()
            msg = _("The file '{}' contains an incompletely created wallet.\n"
                    "Do you want to complete its creation now?").format(path)
            if not self.question(msg):
                if self.question(_("Do you want to delete '{}'?").format(path)):
                    os.remove(path)
                    self.show_warning(_('The file was removed'))
                return
            self.show()
            self.data = json.loads(storage.read())
            self.run(action)
            for k, v in self.data.items():
                db.put(k, v)
            db.write(storage)
            return

        if db.requires_upgrade():
            self.upgrade_db(storage, db)

    def on_error(self, exc_info):
        if not isinstance(exc_info[1], UserCancelled):
            self.logger.error("on_error", exc_info=exc_info)
            self.show_error(str(exc_info[1]))

    def set_icon(self, filename):
        prior_filename, self.icon_filename = self.icon_filename, filename
        self.logo.setPixmap(QPixmap(icon_path(filename))
                            .scaledToWidth(60, mode=Qt.SmoothTransformation))
        return prior_filename

    def set_layout(self, layout, title=None, next_enabled=True):
        self.title.setText("<b>%s</b>"%title if title else "")
        self.title.setVisible(bool(title))
        # Get rid of any prior layout by assigning it to a temporary widget
        prior_layout = self.main_widget.layout()
        if prior_layout:
            QWidget().setLayout(prior_layout)
        self.main_widget.setLayout(layout)
        self.back_button.setEnabled(True)
        self.next_button.setEnabled(next_enabled)
        if next_enabled:
            self.next_button.setFocus()
        self.main_widget.setVisible(True)
        self.please_wait.setVisible(False)

    def exec_layout(self, layout, title=None, raise_on_cancel=True,
                        next_enabled=True, focused_widget=None):
        self.set_layout(layout, title, next_enabled)
        if focused_widget:
            focused_widget.setFocus()
        result = self.loop.exec_()
        if not result and raise_on_cancel:
            raise UserCancelled()
        if result == 1:
            raise GoBack from None
        self.title.setVisible(False)
        self.back_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.main_widget.setVisible(False)
        self.please_wait.setVisible(True)
        self.refresh_gui()
        return result

    def refresh_gui(self):
        # For some reason, to refresh the GUI this needs to be called twice
        self.app.processEvents()
        self.app.processEvents()

    def remove_from_recently_open(self, filename):
        self.config.remove_from_recently_open(filename)

    def text_input(self, title, message, is_valid, allow_multi=False):
        slayout = KeysLayout(parent=self, header_layout=message, is_valid=is_valid,
                             allow_multi=allow_multi, config=self.config)
        self.exec_layout(slayout, title, next_enabled=False)
        return slayout.get_text()

    def seed_input(self, title, message, is_seed, options):
        slayout = SeedLayout(
            title=message,
            is_seed=is_seed,
            options=options,
            parent=self,
            config=self.config,
        )
        self.exec_layout(slayout, title, next_enabled=False)
        return slayout.get_seed(), slayout.seed_type, slayout.is_ext

    @wizard_dialog
    def add_xpub_dialog(self, title, message, is_valid, run_next, allow_multi=False, show_wif_help=False):
        header_layout = QHBoxLayout()
        label = WWLabel(message)
        label.setMinimumWidth(400)
        header_layout.addWidget(label)
        if show_wif_help:
            header_layout.addWidget(InfoButton(WIF_HELP_TEXT), alignment=Qt.AlignRight)
        return self.text_input(title, header_layout, is_valid, allow_multi)

    @wizard_dialog
    def add_cosigner_dialog(self, run_next, index, is_valid):
        title = _("Add Cosigner") + " %d"%index
        message = ' '.join([
            _('Please enter the master public key (xpub) of your cosigner.'),
            _('Enter their master private key (xprv) if you want to be able to sign for them.')
        ])
        return self.text_input(title, message, is_valid)

    @wizard_dialog
    def restore_seed_dialog(self, run_next, test):
        options = []
        if self.opt_ext:
            options.append('ext')
        if self.opt_bip39:
            options.append('bip39')
        if self.opt_slip39:
            options.append('slip39')
        title = _('Enter Seed')
        message = _('Please enter your seed phrase in order to restore your wallet.')
        return self.seed_input(title, message, test, options)

    @wizard_dialog
    def confirm_seed_dialog(self, run_next, seed, test):
        self.app.clipboard().clear()
        title = _('Confirm Seed')
        message = ' '.join([
            _('Your seed is important!'),
            _('If you lose your seed, your money will be permanently lost.'),
            _('To make sure that you have properly saved your seed, please retype it here.')
        ])
        seed, seed_type, is_ext = self.seed_input(title, message, test, None)
        return seed

    @wizard_dialog
    def show_seed_dialog(self, run_next, seed_text):
        title = _("Your wallet generation seed is:")
        slayout = SeedLayout(
            seed=seed_text,
            title=title,
            msg=True,
            options=['ext'],
            config=self.config,
        )
        self.exec_layout(slayout)
        return slayout.is_ext

    def pw_layout(self, msg, kind, force_disable_encrypt_cb):
        pw_layout = PasswordLayout(
            msg=msg, kind=kind, OK_button=self.next_button,
            force_disable_encrypt_cb=force_disable_encrypt_cb)
        pw_layout.encrypt_cb.setChecked(True)
        try:
            self.exec_layout(pw_layout.layout(), focused_widget=pw_layout.new_pw)
            return pw_layout.new_password(), pw_layout.encrypt_cb.isChecked()
        finally:
            pw_layout.clear_password_fields()

    @wizard_dialog
    def request_password(self, run_next, force_disable_encrypt_cb=False):
        """Request the user enter a new password and confirm it.  Return
        the password or None for no password."""
        return self.pw_layout(MSG_ENTER_PASSWORD, PW_NEW, force_disable_encrypt_cb)

    @wizard_dialog
    def request_storage_encryption(self, run_next):
        playout = PasswordLayoutForHW(MSG_HW_STORAGE_ENCRYPTION)
        playout.encrypt_cb.setChecked(True)
        self.exec_layout(playout.layout())
        return playout.encrypt_cb.isChecked()

    @wizard_dialog
    def confirm_dialog(self, title, message, run_next):
        self.confirm(message, title)

    def confirm(self, message, title):
        label = WWLabel(message)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        self.exec_layout(vbox, title)

    @wizard_dialog
    def action_dialog(self, action, run_next):
        self.run(action)

    def terminate(self, **kwargs):
        self.accept_signal.emit()

    def waiting_dialog(self, task, msg, on_finished=None):
        label = WWLabel(msg)
        vbox = QVBoxLayout()
        vbox.addSpacing(100)
        label.setMinimumWidth(300)
        label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(label)
        self.set_layout(vbox, next_enabled=False)
        self.back_button.setEnabled(False)

        t = threading.Thread(target=task)
        t.start()
        while True:
            t.join(1.0/60)
            if t.is_alive():
                self.refresh_gui()
            else:
                break
        if on_finished:
            on_finished()

    def run_task_without_blocking_gui(self, task, *, msg=None):
        assert self.gui_thread == threading.current_thread(), 'must be called from GUI thread'
        if msg is None:
            msg = _("Please wait...")

        exc = None  # type: Optional[Exception]
        res = None
        def task_wrapper():
            nonlocal exc
            nonlocal res
            try:
                res = task()
            except Exception as e:
                exc = e
        self.waiting_dialog(task_wrapper, msg=msg)
        if exc is None:
            return res
        else:
            raise exc

    @wizard_dialog
    def choice_dialog(self, title, message, choices, run_next):
        c_values = [x[0] for x in choices]
        c_titles = [x[1] for x in choices]
        clayout = ChoicesLayout(message, c_titles)
        vbox = QVBoxLayout()
        vbox.addLayout(clayout.layout())
        self.exec_layout(vbox, title)
        action = c_values[clayout.selected_index()]
        return action

    def query_choice(self, msg, choices):
        """called by hardware wallets"""
        clayout = ChoicesLayout(msg, choices)
        vbox = QVBoxLayout()
        vbox.addLayout(clayout.layout())
        self.exec_layout(vbox, '')
        return clayout.selected_index()

    @wizard_dialog
    def derivation_and_script_type_gui_specific_dialog(
            self,
            *,
            title: str,
            message1: str,
            choices: List[Tuple[str, str, str]],
            hide_choices: bool = False,
            message2: str,
            test_text: Callable[[str], int],
            run_next,
            default_choice_idx: int = 0,
            get_account_xpub=None,
    ) -> Tuple[str, str]:
        vbox = QVBoxLayout()

        if get_account_xpub:
            button = QPushButton(_("Detect Existing Accounts"))
            def on_account_select(account):
                script_type = account["script_type"]
                if script_type == "p2pkh":
                    script_type = "standard"
                button_index = c_values.index(script_type)
                button = clayout.group.buttons()[button_index]
                button.setChecked(True)
                line.setText(account["derivation_path"])
            button.clicked.connect(lambda: Bip39RecoveryDialog(self, get_account_xpub, on_account_select))
            vbox.addWidget(button, alignment=Qt.AlignLeft)
            vbox.addWidget(QLabel(_("Or")))

        c_values = [x[0] for x in choices]
        c_titles = [x[1] for x in choices]
        c_default_text = [x[2] for x in choices]
        def on_choice_click(clayout):
            idx = clayout.selected_index()
            line.setText(c_default_text[idx])
        clayout = ChoicesLayout(message1, c_titles, on_choice_click,
                                checked_index=default_choice_idx)
        if not hide_choices:
            vbox.addLayout(clayout.layout())

        vbox.addWidget(WWLabel(message2))

        line = QLineEdit()
        def on_text_change(text):
            self.next_button.setEnabled(test_text(text))
        line.textEdited.connect(on_text_change)
        on_choice_click(clayout)  # set default text for "line"
        vbox.addWidget(line)

        self.exec_layout(vbox, title)
        choice = c_values[clayout.selected_index()]
        return str(line.text()), choice

    @wizard_dialog
    def line_dialog(self, run_next, title, message, default, test, warning='',
                    presets=(), warn_issue4566=False):
        vbox = QVBoxLayout()
        vbox.addWidget(WWLabel(message))
        line = QLineEdit()
        line.setText(default)
        def f(text):
            self.next_button.setEnabled(test(text))
            if warn_issue4566:
                text_whitespace_normalised = ' '.join(text.split())
                warn_issue4566_label.setVisible(text != text_whitespace_normalised)
        line.textEdited.connect(f)
        vbox.addWidget(line)
        vbox.addWidget(WWLabel(warning))

        warn_issue4566_label = WWLabel(MSG_PASSPHRASE_WARN_ISSUE4566)
        warn_issue4566_label.setVisible(False)
        vbox.addWidget(warn_issue4566_label)

        for preset in presets:
            button = QPushButton(preset[0])
            button.clicked.connect(lambda __, text=preset[1]: line.setText(text))
            button.setMinimumWidth(150)
            hbox = QHBoxLayout()
            hbox.addWidget(button, alignment=Qt.AlignCenter)
            vbox.addLayout(hbox)

        self.exec_layout(vbox, title, next_enabled=test(default))
        return line.text()

    @wizard_dialog
    def show_xpub_dialog(self, xpub, run_next):
        msg = ' '.join([
            _("Here is your master public key."),
            _("Please share it with your cosigners.")
        ])
        vbox = QVBoxLayout()
        layout = SeedLayout(
            xpub,
            title=msg,
            icon=False,
            for_seed_words=False,
            config=self.config,
        )
        vbox.addLayout(layout.layout())
        self.exec_layout(vbox, _('Master Public Key'))
        return None

    def init_network(self, network: 'Network'):
        message = _("Electrum communicates with remote servers to get "
                  "information about your transactions and addresses. The "
                  "servers all fulfill the same purpose only differing in "
                  "hardware. In most cases you simply want to let Electrum "
                  "pick one at random.  However if you prefer feel free to "
                  "select a server manually.")
        choices = [_("Auto connect"), _("Select server manually")]
        title = _("How do you want to connect to a server? ")
        clayout = ChoicesLayout(message, choices)
        self.back_button.setText(_('Cancel'))
        self.exec_layout(clayout.layout(), title)
        r = clayout.selected_index()
        if r == 1:
            nlayout = NetworkChoiceLayout(network, self.config, wizard=True)
            if self.exec_layout(nlayout.layout()):
                nlayout.accept()
                self.config.set_key('auto_connect', network.auto_connect, True)
        else:
            network.auto_connect = True
            self.config.set_key('auto_connect', True, True)

    @wizard_dialog
    def multisig_dialog(self, run_next):
        cw = CosignWidget(2, 2)
        n_edit = QSlider(Qt.Horizontal, self)
        m_edit = QSlider(Qt.Horizontal, self)
        n_edit.setMinimum(2)
        n_edit.setMaximum(15)
        m_edit.setMinimum(1)
        m_edit.setMaximum(2)
        n_edit.setValue(2)
        m_edit.setValue(2)
        n_label = QLabel()
        m_label = QLabel()
        grid = QGridLayout()
        grid.addWidget(n_label, 0, 0)
        grid.addWidget(n_edit, 0, 1)
        grid.addWidget(m_label, 1, 0)
        grid.addWidget(m_edit, 1, 1)
        def on_m(m):
            m_label.setText(_('Require {0} signatures').format(m))
            cw.set_m(m)
            backup_warning_label.setVisible(cw.m != cw.n)
        def on_n(n):
            n_label.setText(_('From {0} cosigners').format(n))
            cw.set_n(n)
            m_edit.setMaximum(n)
            backup_warning_label.setVisible(cw.m != cw.n)
        n_edit.valueChanged.connect(on_n)
        m_edit.valueChanged.connect(on_m)
        vbox = QVBoxLayout()
        vbox.addWidget(cw)
        vbox.addWidget(WWLabel(_("Choose the number of signatures needed to unlock funds in your wallet:")))
        vbox.addLayout(grid)
        vbox.addSpacing(2 * char_width_in_lineedit())
        backup_warning_label = WWLabel(_("Warning: to be able to restore a multisig wallet, "
                                         "you should include the master public key for each cosigner "
                                         "in all of your backups."))
        vbox.addWidget(backup_warning_label)
        on_n(2)
        on_m(2)
        self.exec_layout(vbox, _("Multi-Signature Wallet"))
        m = int(m_edit.value())
        n = int(n_edit.value())
        return (m, n)
