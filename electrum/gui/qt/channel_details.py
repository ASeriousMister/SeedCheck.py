from typing import TYPE_CHECKING, Sequence

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QLabel, QLineEdit, QHBoxLayout

from electrum import util
from electrum.i18n import _
from electrum.util import bh2u, format_time
from electrum.lnutil import format_short_channel_id, LOCAL, REMOTE, UpdateAddHtlc, Direction
from electrum.lnchannel import htlcsum, Channel, AbstractChannel, HTLCWithStatus
from electrum.lnaddr import LnAddr, lndecode
from electrum.bitcoin import COIN
from electrum.wallet import Abstract_Wallet

from .util import Buttons, CloseButton, ButtonsLineEdit, MessageBoxMixin, WWLabel

if TYPE_CHECKING:
    from .main_window import ElectrumWindow

class HTLCItem(QtGui.QStandardItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(False)

class SelectableLabel(QtWidgets.QLabel):
    def __init__(self, text=''):
        super().__init__(text)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

class LinkedLabel(QtWidgets.QLabel):
    def __init__(self, text, on_clicked):
        super().__init__(text)
        self.linkActivated.connect(on_clicked)


class ChannelDetailsDialog(QtWidgets.QDialog, MessageBoxMixin):
    def make_htlc_item(self, i: UpdateAddHtlc, direction: Direction) -> HTLCItem:
        it = HTLCItem(_('Sent HTLC with ID {}' if Direction.SENT == direction else 'Received HTLC with ID {}').format(i.htlc_id))
        it.appendRow([HTLCItem(_('Amount')),HTLCItem(self.format_msat(i.amount_msat))])
        it.appendRow([HTLCItem(_('CLTV expiry')),HTLCItem(str(i.cltv_expiry))])
        it.appendRow([HTLCItem(_('Payment hash')),HTLCItem(bh2u(i.payment_hash))])
        return it

    def make_model(self, htlcs: Sequence[HTLCWithStatus]) -> QtGui.QStandardItemModel:
        model = QtGui.QStandardItemModel(0, 2)
        model.setHorizontalHeaderLabels(['HTLC', 'Property value'])
        parentItem = model.invisibleRootItem()
        folder_types = {
            'settled': _('Fulfilled HTLCs'),
            'inflight': _('HTLCs in current commitment transaction'),
            'failed': _('Failed HTLCs'),
        }
        self.folders = {}
        self.keyname_rows = {}

        for keyname, i in folder_types.items():
            myFont=QtGui.QFont()
            myFont.setBold(True)
            folder = HTLCItem(i)
            folder.setFont(myFont)
            parentItem.appendRow(folder)
            self.folders[keyname] = folder
            mapping = {}
            num = 0
            for htlc_with_status in htlcs:
                if htlc_with_status.status != keyname:
                    continue
                htlc = htlc_with_status.htlc
                it = self.make_htlc_item(htlc, htlc_with_status.direction)
                self.folders[keyname].appendRow(it)
                mapping[htlc.payment_hash] = num
                num += 1
            self.keyname_rows[keyname] = mapping
        return model

    def move(self, fro: str, to: str, payment_hash: bytes):
        assert fro != to
        row_idx = self.keyname_rows[fro].pop(payment_hash)
        row = self.folders[fro].takeRow(row_idx)
        self.folders[to].appendRow(row)
        dest_mapping = self.keyname_rows[to]
        dest_mapping[payment_hash] = len(dest_mapping)

    htlc_fulfilled = QtCore.pyqtSignal(str, bytes, Channel, int)
    htlc_failed = QtCore.pyqtSignal(str, bytes, Channel, int)
    htlc_added = QtCore.pyqtSignal(str, Channel, UpdateAddHtlc, Direction)
    state_changed = QtCore.pyqtSignal(str, Abstract_Wallet, AbstractChannel)

    @QtCore.pyqtSlot(str, Abstract_Wallet, AbstractChannel)
    def do_state_changed(self, wallet, chan):
        if wallet != self.wallet:
            return
        if chan == self.chan:
            self.update()

    @QtCore.pyqtSlot(str, Channel, UpdateAddHtlc, Direction)
    def on_htlc_added(self, evtname, chan, htlc, direction):
        if chan != self.chan:
            return
        mapping = self.keyname_rows['inflight']
        mapping[htlc.payment_hash] = len(mapping)
        self.folders['inflight'].appendRow(self.make_htlc_item(htlc, direction))

    @QtCore.pyqtSlot(str, bytes, Channel, int)
    def on_htlc_fulfilled(self, evtname, payment_hash, chan, htlc_id):
        if chan.channel_id != self.chan.channel_id:
            return
        self.move('inflight', 'settled', payment_hash)
        self.update()

    @QtCore.pyqtSlot(str, bytes, Channel, int)
    def on_htlc_failed(self, evtname, payment_hash, chan, htlc_id):
        if chan.channel_id != self.chan.channel_id:
            return
        self.move('inflight', 'failed', payment_hash)
        self.update()

    def update(self):
        self.can_send_label.setText(self.format_msat(self.chan.available_to_spend(LOCAL)))
        self.can_receive_label.setText(self.format_msat(self.chan.available_to_spend(REMOTE)))
        self.sent_label.setText(self.format_msat(self.chan.total_msat(Direction.SENT)))
        self.received_label.setText(self.format_msat(self.chan.total_msat(Direction.RECEIVED)))
        self.local_balance_label.setText(self.format_msat(self.chan.balance(LOCAL)))
        self.remote_balance_label.setText(self.format_msat(self.chan.balance(REMOTE)))

    @QtCore.pyqtSlot(str)
    def show_tx(self, link_text: str):
        funding_tx = self.wallet.db.get_transaction(self.chan.funding_outpoint.txid)
        if not funding_tx:
            self.show_error(_("Funding transaction not found."))
            return
        self.window.show_transaction(funding_tx, tx_desc=_('Funding Transaction'))

    def __init__(self, window: 'ElectrumWindow', chan_id: bytes):
        super().__init__(window)

        # initialize instance fields
        self.window = window
        self.wallet = window.wallet
        chan = self.chan = window.wallet.lnworker.channels[chan_id]
        self.format_msat = lambda msat: window.format_amount_and_units(msat / 1000)
        self.format_sat = lambda sat: window.format_amount_and_units(sat)

        # connect signals with slots
        self.htlc_fulfilled.connect(self.on_htlc_fulfilled)
        self.htlc_failed.connect(self.on_htlc_failed)
        self.state_changed.connect(self.do_state_changed)
        self.htlc_added.connect(self.on_htlc_added)

        # register callbacks for updating
        util.register_callback(self.htlc_fulfilled.emit, ['htlc_fulfilled'])
        util.register_callback(self.htlc_failed.emit, ['htlc_failed'])
        util.register_callback(self.htlc_added.emit, ['htlc_added'])
        util.register_callback(self.state_changed.emit, ['channel'])

        # set attributes of QDialog
        self.setWindowTitle(_('Channel Details'))
        self.setMinimumSize(800, 400)

        # add layouts
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(QLabel(_('Remote Node ID:')))
        remote_id_e = ButtonsLineEdit(bh2u(chan.node_id))
        remote_id_e.addCopyButton(self.window.app)
        remote_id_e.setReadOnly(True)
        vbox.addWidget(remote_id_e)
        funding_label_text = f'<a href=click_destination>{chan.funding_outpoint.txid}</a>:{chan.funding_outpoint.output_index}'
        vbox.addWidget(QLabel(_('Funding Outpoint:')))
        vbox.addWidget(LinkedLabel(funding_label_text, self.show_tx))

        hbox_stats = QHBoxLayout()

        # channel stats left column
        form_layout_left = QtWidgets.QFormLayout(None)
        form_layout_left.addRow(_('Channel ID:'), WWLabel(f"{chan.channel_id.hex()} (Short: {chan.short_channel_id})"))
        form_layout_left.addRow(_('State:'), SelectableLabel(chan.get_state_for_GUI()))
        self.initiator = 'Local' if chan.constraints.is_initiator else 'Remote'
        form_layout_left.addRow(_('Initiator:'), SelectableLabel(self.initiator))
        self.capacity = self.format_sat(chan.get_capacity())
        form_layout_left.addRow(_('Capacity:'), SelectableLabel(self.capacity))
        self.can_send_label = SelectableLabel()
        self.can_receive_label = SelectableLabel()
        form_layout_left.addRow(_('Can send:'), self.can_send_label)
        form_layout_left.addRow(_('Can receive:'), self.can_receive_label)
        #self.htlc_minimum_msat = SelectableLabel(str(chan.config[REMOTE].htlc_minimum_msat))
        #form_layout_left.addRow(_('Minimum HTLC value accepted by peer (mSAT):'), self.htlc_minimum_msat)
        #self.max_htlcs = SelectableLabel(str(chan.config[REMOTE].max_accepted_htlcs))
        #form_layout_left.addRow(_('Maximum number of concurrent HTLCs accepted by peer:'), self.max_htlcs)
        #self.max_htlc_value = SelectableLabel(self.format_sat(chan.config[REMOTE].max_htlc_value_in_flight_msat / 1000))
        #form_layout_left.addRow(_('Maximum value of in-flight HTLCs accepted by peer:'), self.max_htlc_value)
        dust_limit_label = SelectableLabel("{}, {}".format(
            self.format_sat(chan.config[REMOTE].dust_limit_sat),
            self.format_sat(chan.config[LOCAL].dust_limit_sat),
        ))
        form_layout_left.addRow(_('Dust limit:'), dust_limit_label)
        chan_reserve_label = SelectableLabel("{}, {}".format(
            self.format_sat(chan.config[REMOTE].reserve_sat),
            self.format_sat(chan.config[LOCAL].reserve_sat),
        ))
        form_layout_left.addRow(_('Channel reserve:'), chan_reserve_label)
        form_layout_left.addRow(_('Channel type:'), SelectableLabel(chan.storage['channel_type'].name_minimal))
        hbox_stats.addLayout(form_layout_left, 50)

        # vertical line separator
        line_separator = QtWidgets.QFrame()
        line_separator.setFrameShape(QtWidgets.QFrame.VLine)
        line_separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        line_separator.setLineWidth(1)
        hbox_stats.addWidget(line_separator)

        # channel stats right column
        form_layout_right = QtWidgets.QFormLayout(None)
        self.local_balance_label = SelectableLabel()
        self.remote_balance_label = SelectableLabel()
        form_layout_right.addRow(_('Local balance:'), self.local_balance_label)
        form_layout_right.addRow(_('Remote balance:'), self.remote_balance_label)
        self.received_label = SelectableLabel()
        self.sent_label = SelectableLabel()
        form_layout_right.addRow(_('Total received so far:'), self.received_label)
        form_layout_right.addRow(_('Total sent so far:'), self.sent_label)
        hbox_stats.addLayout(form_layout_right, 50)

        vbox.addLayout(hbox_stats)

        # add htlc tree view to vbox (wouldn't scale correctly in QFormLayout)
        vbox.addWidget(QLabel(_('Payments (HTLCs):')))
        w = QtWidgets.QTreeView(self)
        htlc_dict = chan.get_payments()
        htlc_list = []
        for rhash, plist in htlc_dict.items():
            for htlc_with_status in plist:
                htlc_list.append(htlc_with_status)
        w.setModel(self.make_model(htlc_list))
        w.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        vbox.addWidget(w)
        vbox.addLayout(Buttons(CloseButton(self)))
        # initialize sent/received fields
        self.update()
