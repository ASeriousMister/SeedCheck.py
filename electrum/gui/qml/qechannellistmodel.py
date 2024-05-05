from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex
from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot

from electrum.lnchannel import ChannelState
from electrum.lnutil import LOCAL, REMOTE
from electrum.logging import get_logger
from electrum.util import Satoshis
from electrum.gui import messages

from .qetypes import QEAmount
from .util import QtEventListener, qt_event_listener
from .qemodelfilter import QEFilterProxyModel


class QEChannelListModel(QAbstractListModel, QtEventListener):
    _logger = get_logger(__name__)

    # define listmodel rolemap
    _ROLE_NAMES=('cid', 'state', 'state_code', 'initiator', 'capacity', 'can_send',
                 'can_receive', 'l_csv_delay', 'r_csv_delay', 'send_frozen', 'receive_frozen',
                 'type', 'node_id', 'node_alias', 'short_cid', 'funding_tx', 'is_trampoline',
                 'is_backup', 'is_imported', 'local_capacity', 'remote_capacity')
    _ROLE_KEYS = range(Qt.ItemDataRole.UserRole, Qt.ItemDataRole.UserRole + len(_ROLE_NAMES))
    _ROLE_MAP  = dict(zip(_ROLE_KEYS, [bytearray(x.encode()) for x in _ROLE_NAMES]))
    _ROLE_RMAP = dict(zip(_ROLE_NAMES, _ROLE_KEYS))

    _network_signal = pyqtSignal(str, object)

    def __init__(self, wallet, parent=None):
        super().__init__(parent)
        self.wallet = wallet
        self._channels = []

        self._fm_backups = None
        self._fm_nobackups = None

        self.initModel()

        # To avoid leaking references to "self" that prevent the
        # window from being GC-ed when closed, callbacks should be
        # methods of this class only, and specifically not be
        # partials, lambdas or methods of subobjects.  Hence...
        self.register_callbacks()
        self.destroyed.connect(lambda: self.on_destroy())

    @qt_event_listener
    def on_event_channel(self, wallet, channel):
        if wallet == self.wallet:
            self.on_channel_updated(channel)

    @qt_event_listener
    def on_event_channels_updated(self, wallet):
        if wallet == self.wallet:
            self.initModel()

    def on_destroy(self):
        self.unregister_callbacks()

    def rowCount(self, index):
        return len(self._channels)

    # also expose rowCount as a property
    countChanged = pyqtSignal()
    @pyqtProperty(int, notify=countChanged)
    def count(self):
        return len(self._channels)

    def roleNames(self):
        return self._ROLE_MAP

    def data(self, index, role):
        tx = self._channels[index.row()]
        role_index = role - Qt.ItemDataRole.UserRole
        value = tx[self._ROLE_NAMES[role_index]]
        if isinstance(value, (bool, list, int, str, QEAmount)) or value is None:
            return value
        if isinstance(value, Satoshis):
            return value.value
        return str(value)

    def clear(self):
        self.beginResetModel()
        self._channels = []
        self.endResetModel()

    def channel_to_model(self, lnc):
        lnworker = self.wallet.lnworker
        item = {
            'cid': lnc.channel_id.hex(),
            'node_id': lnc.node_id.hex(),
            'node_alias': lnworker.get_node_alias(lnc.node_id) or '',
            'short_cid': lnc.short_id_for_GUI(),
            'state': lnc.get_state_for_GUI(),
            'state_code': int(lnc.get_state()),
            'is_backup': lnc.is_backup(),
            'is_trampoline': lnworker.is_trampoline_peer(lnc.node_id),
            'capacity': QEAmount(amount_sat=lnc.get_capacity())
        }
        if lnc.is_backup():
            item['can_send'] = QEAmount()
            item['can_receive'] = QEAmount()
            item['local_capacity'] = QEAmount()
            item['remote_capacity'] = QEAmount()
            item['send_frozen'] = True
            item['receive_frozen'] = True
            item['is_imported'] = lnc.is_imported
        else:
            item['can_send'] = QEAmount(amount_msat=lnc.available_to_spend(LOCAL))
            item['can_receive'] = QEAmount(amount_msat=lnc.available_to_spend(REMOTE))
            item['local_capacity'] = QEAmount(amount_msat=lnc.balance(LOCAL))
            item['remote_capacity'] = QEAmount(amount_msat=lnc.balance(REMOTE))
            item['send_frozen'] = lnc.is_frozen_for_sending()
            item['receive_frozen'] = lnc.is_frozen_for_receiving()
            item['is_imported'] = False
        return item

    numOpenChannelsChanged = pyqtSignal()
    @pyqtProperty(int, notify=numOpenChannelsChanged)
    def numOpenChannels(self):
        return sum([1 if x['state_code'] == ChannelState.OPEN else 0 for x in self._channels])

    @pyqtSlot()
    def initModel(self):
        self._logger.debug('init_model')
        if not self.wallet.lnworker:
            self._logger.warning('lnworker should be defined')
            return

        channels = []

        lnchannels = self.wallet.lnworker.get_channel_objects()
        for channel in lnchannels.values():
            item = self.channel_to_model(channel)
            channels.append(item)

        # sort, for now simply by state
        def chan_sort_score(c):
            return c['state_code'] + (10 if c['is_backup'] else 0)
        channels.sort(key=chan_sort_score)

        self.clear()
        self.beginInsertRows(QModelIndex(), 0, len(channels) - 1)
        self._channels = channels
        self.endInsertRows()

        self.countChanged.emit()

    def on_channel_updated(self, channel):
        for i, c in enumerate(self._channels):
            if c['cid'] == channel.channel_id.hex():
                self.do_update(i, channel)
                break

    def do_update(self, modelindex, channel):
        self._logger.debug(f'updating our channel {channel.short_id_for_GUI()}')
        modelitem = self._channels[modelindex]
        modelitem.update(self.channel_to_model(channel))

        mi = self.createIndex(modelindex, 0)
        self.dataChanged.emit(mi, mi, self._ROLE_KEYS)
        self.numOpenChannelsChanged.emit()

    @pyqtSlot(str)
    def newChannel(self, cid):
        self._logger.debug('new channel with cid %s' % cid)
        lnchannels = self.wallet.lnworker.channels
        for channel in lnchannels.values():
            if cid == channel.channel_id.hex():
                item = self.channel_to_model(channel)
                self._logger.debug(item)
                self.beginInsertRows(QModelIndex(), 0, 0)
                self._channels.insert(0, item)
                self.endInsertRows()
                self.countChanged.emit()
                return

    @pyqtSlot(str)
    def removeChannel(self, cid):
        self._logger.debug('remove channel with cid %s' % cid)
        for i, channel in enumerate(self._channels):
            if cid == channel['cid']:
                self._logger.debug(cid)
                self.beginRemoveRows(QModelIndex(), i, i)
                self._channels.remove(channel)
                self.endRemoveRows()
                self.countChanged.emit()
                return

    def filterModel(self, role, match):
        _filterModel = QEFilterProxyModel(self, self)
        assert role in self._ROLE_RMAP
        _filterModel.setFilterRole(self._ROLE_RMAP[role])
        _filterModel.setFilterValue(match)
        return _filterModel

    @pyqtSlot(result=QEFilterProxyModel)
    def filterModelBackups(self):
        self._fm_backups = self.filterModel('is_backup', True)
        return self._fm_backups

    @pyqtSlot(result=QEFilterProxyModel)
    def filterModelNoBackups(self):
        self._fm_nobackups = self.filterModel('is_backup', False)
        return self._fm_nobackups

    @pyqtSlot(result=str)
    def lightningWarningMessage(self):
        return messages.MSG_LIGHTNING_WARNING
