import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

import org.electrum 1.0

import "controls"

Item {
    id: root
    clip: true
    implicitHeight: 0

    function open() {
        state = 'opened'
    }
    function close() {
        state = ''
    }
    function toggle() {
        if (state == 'opened')
            state = ''
        else
            state = 'opened'
    }

    states: [
        State {
            name: 'opened'
            PropertyChanges { target: root; implicitHeight: detailsPane.height }
        }
    ]

    transitions: [
        Transition {
            from: ''
            to: 'opened'
            NumberAnimation { target: root; properties: 'implicitHeight'; duration: 200 }
        },
        Transition {
            from: 'opened'
            to: ''
            NumberAnimation { target: root; properties: 'implicitHeight'; duration: 100 }
        }
    ]

    Pane {
        id: detailsPane
        width: parent.width
        anchors.bottom: parent.bottom
        padding: 0
        background: Rectangle {
            color: Material.dialogColor
        }

        ColumnLayout {
            id: rootLayout
            width: parent.width
            spacing: constants.paddingXLarge

            Item { Layout.preferredWidth: 1; Layout.preferredHeight: 1 }

            RowLayout {
                Layout.fillWidth: true
                FlatButton {
                    text: qsTr('More details')
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    enabled: app.stack.currentItem.objectName != 'WalletDetails'
                    onClicked: {
                        root.close()
                        app.stack.pushOnRoot(Qt.resolvedUrl('WalletDetails.qml'))
                    }
                }
                FlatButton {
                    text: qsTr('Switch wallet')
                    Layout.fillWidth: true
                    icon.source: '../../icons/file.png'
                    Layout.preferredWidth: 1
                    enabled: app.stack.currentItem.objectName != 'Wallets'
                    onClicked: {
                        root.close()
                        app.stack.pushOnRoot(Qt.resolvedUrl('Wallets.qml'))
                    }
                }
            }
        }
    }

    property string formattedTotalBalance
    property string formattedTotalBalanceFiat

    function setBalances() {
        root.formattedTotalBalance = Config.formatSats(Daemon.currentWallet.totalBalance)
        if (Daemon.fx.enabled) {
            root.formattedTotalBalanceFiat = Daemon.fx.fiatValue(Daemon.currentWallet.totalBalance, false)
        }
    }


    // instead of all these explicit connections, we should expose
    // formatted balances directly as a property
    Connections {
        target: Config
        function onBaseUnitChanged() { setBalances() }
        function onThousandsSeparatorChanged() { setBalances() }
    }

    Connections {
        target: Daemon
        function onWalletLoaded() { setBalances() }
    }

    Connections {
        target: Daemon.fx
        function onEnabledUpdated() { setBalances() }
        function onQuotesUpdated() { setBalances() }
    }

    Connections {
        target: Daemon.currentWallet
        function onBalanceChanged() {
            setBalances()
        }
    }

}
