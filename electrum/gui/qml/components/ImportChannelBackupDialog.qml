import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

import org.electrum 1.0

import "controls"

ElDialog {
    id: root

    property bool valid: false

    width: parent.width
    height: parent.height

    padding: 0

    title: qsTr('Import channel backup')
    iconSource: Qt.resolvedUrl('../../icons/file.png')

    function verifyChannelBackup(text) {
        return valid = Daemon.currentWallet.isValidChannelBackup(text)
    }

    onAccepted: {
        Daemon.currentWallet.importChannelBackup(channelbackup_ta.text)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: constants.paddingLarge

            TextArea {
                id: channelbackup_ta
                Layout.fillWidth: true
                Layout.minimumHeight: 80
                font.family: FixedFont
                focus: true
                wrapMode: TextEdit.WrapAnywhere
                onTextChanged: verifyChannelBackup(text)
            }
            ColumnLayout {
                ToolButton {
                    icon.source: '../../icons/paste.png'
                    icon.height: constants.iconSizeMedium
                    icon.width: constants.iconSizeMedium
                    onClicked: {
                        channelbackup_ta.text = AppController.clipboardToText()
                    }
                }
                ToolButton {
                    icon.source: '../../icons/qrcode.png'
                    icon.height: constants.iconSizeMedium
                    icon.width: constants.iconSizeMedium
                    scale: 1.2
                    onClicked: {
                        var dialog = app.scanDialog.createObject(app, {
                            hint:  qsTr('Scan a channel backup')
                        })
                        dialog.onFound.connect(function() {
                            channelbackup_ta.text = dialog.scanData
                            dialog.close()
                        })
                        dialog.open()
                    }
                }
            }
        }

        TextArea {
            id: validationtext
            visible: text
            Layout.fillWidth: true
            Layout.leftMargin: constants.paddingLarge

            readOnly: true
            wrapMode: TextInput.WordWrap
            background: Rectangle {
                color: 'transparent'
            }
        }

        Item { Layout.preferredWidth: 1; Layout.fillHeight: true }

        FlatButton {
            Layout.fillWidth: true
            enabled: valid
            text: qsTr('Import')
            onClicked: doAccept()
        }
    }

}
