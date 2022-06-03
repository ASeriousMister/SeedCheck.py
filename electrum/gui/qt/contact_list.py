#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2015 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from enum import IntEnum

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QPersistentModelIndex, QModelIndex
from PyQt5.QtWidgets import (QAbstractItemView, QMenu)

from electrum.i18n import _
from electrum.bitcoin import is_address
from electrum.util import block_explorer_URL
from electrum.plugin import run_hook

from .util import MyTreeView, webopen


class ContactList(MyTreeView):

    class Columns(IntEnum):
        NAME = 0
        ADDRESS = 1

    headers = {
        Columns.NAME: _('Name'),
        Columns.ADDRESS: _('Address'),
    }
    filter_columns = [Columns.NAME, Columns.ADDRESS]

    ROLE_CONTACT_KEY = Qt.UserRole + 1000
    key_role = ROLE_CONTACT_KEY

    def __init__(self, parent):
        super().__init__(parent, self.create_menu,
                         stretch_column=self.Columns.NAME,
                         editable_columns=[self.Columns.NAME])
        self.setModel(QStandardItemModel(self))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.std_model = self.model()
        self.update()

    def on_edited(self, idx, edit_key, *, text):
        _type, prior_name = self.parent.contacts.pop(edit_key)
        self.parent.set_contact(text, edit_key)
        self.update()

    def create_menu(self, position):
        menu = QMenu()
        idx = self.indexAt(position)
        column = idx.column() or self.Columns.NAME
        selected_keys = []
        for s_idx in self.selected_in_column(self.Columns.NAME):
            sel_key = self.model().itemFromIndex(s_idx).data(self.ROLE_CONTACT_KEY)
            selected_keys.append(sel_key)
        if not selected_keys or not idx.isValid():
            menu.addAction(_("New contact"), lambda: self.parent.new_contact_dialog())
            menu.addAction(_("Import file"), lambda: self.parent.import_contacts())
            menu.addAction(_("Export file"), lambda: self.parent.export_contacts())
        else:
            column_title = self.model().horizontalHeaderItem(column).text()
            column_data = '\n'.join(self.model().itemFromIndex(s_idx).text()
                                    for s_idx in self.selected_in_column(column))
            menu.addAction(_("Copy {}").format(column_title), lambda: self.place_text_on_clipboard(column_data, title=column_title))
            if column in self.editable_columns:
                item = self.model().itemFromIndex(idx)
                if item.isEditable():
                    # would not be editable if openalias
                    persistent = QPersistentModelIndex(idx)
                    menu.addAction(_("Edit {}").format(column_title), lambda p=persistent: self.edit(QModelIndex(p)))
            menu.addAction(_("Pay to"), lambda: self.parent.payto_contacts(selected_keys))
            menu.addAction(_("Delete"), lambda: self.parent.delete_contacts(selected_keys))
            URLs = [block_explorer_URL(self.config, 'addr', key) for key in filter(is_address, selected_keys)]
            if URLs:
                menu.addAction(_("View on block explorer"), lambda: [webopen(u) for u in URLs])

        run_hook('create_contact_menu', menu, selected_keys)
        menu.exec_(self.viewport().mapToGlobal(position))

    def update(self):
        if self.maybe_defer_update():
            return
        current_key = self.get_role_data_for_current_item(col=self.Columns.NAME, role=self.ROLE_CONTACT_KEY)
        self.model().clear()
        self.update_headers(self.__class__.headers)
        set_current = None
        for key in sorted(self.parent.contacts.keys()):
            contact_type, name = self.parent.contacts[key]
            items = [QStandardItem(x) for x in (name, key)]
            items[self.Columns.NAME].setEditable(contact_type != 'openalias')
            items[self.Columns.ADDRESS].setEditable(False)
            items[self.Columns.NAME].setData(key, self.ROLE_CONTACT_KEY)
            row_count = self.model().rowCount()
            self.model().insertRow(row_count, items)
            if key == current_key:
                idx = self.model().index(row_count, self.Columns.NAME)
                set_current = QPersistentModelIndex(idx)
        self.set_current_idx(set_current)
        # FIXME refresh loses sort order; so set "default" here:
        self.sortByColumn(self.Columns.NAME, Qt.AscendingOrder)
        self.filter()
        run_hook('update_contacts_tab', self)

    def refresh_row(self, key, row):
        # nothing to update here
        pass

    def get_edit_key_from_coordinate(self, row, col):
        if col != self.Columns.NAME:
            return None
        return self.get_role_data_from_coordinate(row, col, role=self.ROLE_CONTACT_KEY)
