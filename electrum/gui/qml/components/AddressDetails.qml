import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

import org.electrum 1.0

import "controls"

Pane {
    id: root
    width: parent.width
    height: parent.height
    padding: 0

    property string address

    signal addressDetailsChanged
    signal addressDeleted

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true

            leftMargin: constants.paddingLarge
            rightMargin: constants.paddingLarge
            topMargin: constants.paddingLarge

            contentHeight: rootLayout.height
            clip:true
            interactive: height < contentHeight

            GridLayout {
                id: rootLayout
                width: parent.width

                columns: 2

                Heading {
                    Layout.columnSpan: 2
                    text: qsTr('Address details')
                }

                RowLayout {
                    Layout.columnSpan: 2
                    Label {
                        text: qsTr('Address')
                        color: Material.accentColor
                    }

                    Tag {
                        visible: addressdetails.isFrozen
                        text: qsTr('Frozen')
                        labelcolor: 'white'
                    }
                }

                TextHighlightPane {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true

                    RowLayout {
                        width: parent.width
                        Label {
                            text: root.address
                            font.pixelSize: constants.fontSizeLarge
                            font.family: FixedFont
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                        }
                        ToolButton {
                            icon.source: '../../icons/share.png'
                            icon.color: 'transparent'
                            onClicked: {
                                var dialog = app.genericShareDialog.createObject(root,
                                    { title: qsTr('Address'), text: root.address }
                                )
                                dialog.open()
                            }
                        }
                    }
                }

                Label {
                    text: qsTr('Balance')
                    color: Material.accentColor
                }

                FormattedAmount {
                    amount: addressdetails.balance
                }

                Label {
                    text: qsTr('Transactions')
                    color: Material.accentColor
                }

                Label {
                    text: addressdetails.numTx
                }

                Label {
                    Layout.columnSpan: 2
                    Layout.topMargin: constants.paddingSmall
                    text: qsTr('Label')
                    color: Material.accentColor
                }

                TextHighlightPane {
                    id: labelContent

                    property bool editmode: false

                    Layout.columnSpan: 2
                    Layout.fillWidth: true

                    RowLayout {
                        width: parent.width
                        Label {
                            visible: !labelContent.editmode
                            text: addressdetails.label
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            font.pixelSize: constants.fontSizeLarge
                        }
                        ToolButton {
                            visible: !labelContent.editmode
                            icon.source: '../../icons/pen.png'
                            icon.color: 'transparent'
                            onClicked: {
                                labelEdit.text = addressdetails.label
                                labelContent.editmode = true
                                labelEdit.focus = true
                            }
                        }
                        TextField {
                            id: labelEdit
                            visible: labelContent.editmode
                            text: addressdetails.label
                            font.pixelSize: constants.fontSizeLarge
                            Layout.fillWidth: true
                        }
                        ToolButton {
                            visible: labelContent.editmode
                            icon.source: '../../icons/confirmed.png'
                            icon.color: 'transparent'
                            onClicked: {
                                labelContent.editmode = false
                                addressdetails.setLabel(labelEdit.text)
                            }
                        }
                        ToolButton {
                            visible: labelContent.editmode
                            icon.source: '../../icons/closebutton.png'
                            icon.color: 'transparent'
                            onClicked: labelContent.editmode = false
                        }
                    }
                }

                Heading {
                    Layout.columnSpan: 2
                    text: qsTr('Technical Properties')
                }

                Label {
                    Layout.topMargin: constants.paddingSmall
                    text: qsTr('Script type')
                    color: Material.accentColor
                }

                Label {
                    Layout.topMargin: constants.paddingSmall
                    Layout.fillWidth: true
                    text: addressdetails.scriptType
                }

                Label {
                    visible: addressdetails.derivationPath
                    text: qsTr('Derivation path')
                    color: Material.accentColor
                }

                Label {
                    visible: addressdetails.derivationPath
                    text: addressdetails.derivationPath
                }

                Label {
                    Layout.columnSpan: 2
                    Layout.topMargin: constants.paddingSmall
                    visible: addressdetails.pubkeys.length
                    text: addressdetails.pubkeys.length > 1
                        ? qsTr('Public keys')
                        : qsTr('Public key')
                    color: Material.accentColor
                }

                Repeater {
                    model: addressdetails.pubkeys
                    delegate: TextHighlightPane {
                        Layout.columnSpan: 2
                        Layout.fillWidth: true

                        RowLayout {
                            width: parent.width
                            Label {
                                text: modelData
                                Layout.fillWidth: true
                                wrapMode: Text.Wrap
                                font.pixelSize: constants.fontSizeLarge
                                font.family: FixedFont
                            }
                            ToolButton {
                                icon.source: '../../icons/share.png'
                                enabled: modelData
                                onClicked: {
                                    var dialog = app.genericShareDialog.createObject(root, {
                                        title: qsTr('Public key'),
                                        text: modelData
                                    })
                                    dialog.open()
                                }
                            }
                        }
                    }
                }

                Label {
                    Layout.columnSpan: 2
                    Layout.topMargin: constants.paddingSmall
                    visible: !Daemon.currentWallet.isWatchOnly
                    text: qsTr('Private key')
                    color: Material.accentColor
                }

                TextHighlightPane {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                    visible: !Daemon.currentWallet.isWatchOnly
                    RowLayout {
                        width: parent.width
                        Label {
                            id: privateKeyText
                            Layout.fillWidth: true
                            visible: addressdetails.privkey
                            text: addressdetails.privkey
                            wrapMode: Text.Wrap
                            font.pixelSize: constants.fontSizeLarge
                            font.family: FixedFont
                        }
                        Label {
                            id: showPrivateKeyText
                            Layout.fillWidth: true
                            visible: !addressdetails.privkey
                            horizontalAlignment: Text.AlignHCenter
                            text: qsTr('Tap to show private key')
                            wrapMode: Text.Wrap
                            font.pixelSize: constants.fontSizeLarge
                        }
                        ToolButton {
                            icon.source: '../../icons/share.png'
                            visible: addressdetails.privkey
                            onClicked: {
                                var dialog = app.genericShareDialog.createObject(root, {
                                    title: qsTr('Private key'),
                                    text: addressdetails.privkey
                                })
                                dialog.open()
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            enabled: !addressdetails.privkey
                            onClicked: addressdetails.requestShowPrivateKey()
                        }
                    }
                }
            }
        }

        ButtonContainer {
            Layout.fillWidth: true
            FlatButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: addressdetails.isFrozen ? qsTr('Unfreeze address') : qsTr('Freeze address')
                onClicked: addressdetails.freeze(!addressdetails.isFrozen)
                icon.source: '../../icons/freeze.png'
            }
            FlatButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                visible: Daemon.currentWallet.canSignMessage
                text: qsTr('Sign/Verify')
                icon.source: '../../icons/pen.png'
                onClicked: {
                    var dialog = app.signVerifyMessageDialog.createObject(app, {
                        address: root.address
                    })
                    dialog.open()
                }
            }
            FlatButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                visible: addressdetails.canDelete
                text: qsTr('Delete')
                onClicked: {
                    var confirmdialog = app.messageDialog.createObject(root, {
                        text: qsTr('Are you sure you want to delete this address from the wallet?'),
                        yesno: true
                    })
                    confirmdialog.accepted.connect(function () {
                        var success = addressdetails.deleteAddress()
                        if (success) {
                            addressDeleted()
                            app.stack.pop()
                        }
                    })
                    confirmdialog.open()
                }
                icon.source: '../../icons/delete.png'
            }
        }
    }

    AddressDetails {
        id: addressdetails
        wallet: Daemon.currentWallet
        address: root.address
        onFrozenChanged: addressDetailsChanged()
        onLabelChanged: addressDetailsChanged()
        onAuthRequired: (method, authMessage) => {
            app.handleAuthRequired(addressdetails, method, authMessage)
        }
        onAddressDeleteFailed: (message) => {
            var dialog = app.messageDialog.createObject(root, {
                text: message
            })
            dialog.open()
        }
    }
}
