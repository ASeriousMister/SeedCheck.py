import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

import org.electrum 1.0

import "../controls"

WizardComponent {
    valid: true

    property string masterPubkey: wizard_data['multisig_master_pubkey']

    ColumnLayout {
        width: parent.width

        Label {
            text: qsTr('Here is your master public key. Please share it with your cosigners')
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        TextHighlightPane {
            Layout.fillWidth: true

            RowLayout {
                width: parent.width
                Label {
                    Layout.fillWidth: true
                    text: masterPubkey
                    font.pixelSize: constants.fontSizeMedium
                    font.family: FixedFont
                    wrapMode: Text.Wrap
                }
                ToolButton {
                    icon.source: '../../../icons/share.png'
                    icon.color: 'transparent'
                    onClicked: {
                        var dialog = app.genericShareDialog.createObject(app,
                            { title: qsTr('Master public key'), text: masterPubkey }
                        )
                        dialog.open()
                    }
                }
            }
        }
    }

}
