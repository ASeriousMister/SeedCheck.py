import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

import org.electrum 1.0


Item {
    id: root

    property bool showAutoselectServer: true
    property alias auto_connect: auto_server_cb.checked
    property alias address: address_tf.text

    implicitHeight: rootLayout.height

    ColumnLayout {
        id: rootLayout

        width: parent.width
        height: parent.height
        spacing: constants.paddingLarge

        CheckBox {
            id: auto_server_cb
            visible: showAutoselectServer
            text: qsTr('Select server automatically')
            checked: true
        }

        Label {
            text: qsTr("Server")
            enabled: address_tf.enabled
        }

        TextHighlightPane {
            Layout.fillWidth: true

            TextField {
                id: address_tf
                enabled: !auto_server_cb.checked
                width: parent.width
                inputMethodHints: Qt.ImhNoPredictiveText
            }
        }

        ColumnLayout {
            Heading {
                text: qsTr('Servers')
            }

            Frame {
                background: PaneInsetBackground { baseColor: Material.dialogColor }
                clip: true
                verticalPadding: 0
                horizontalPadding: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.bottomMargin: constants.paddingLarge

                ElListView {
                    id: serversListView
                    anchors.fill: parent
                    model: Network.serverListModel
                    delegate: ServerDelegate {
                        onClicked: {
                            address_tf.text = model.name
                        }
                    }

                    section.property: 'chain'
                    section.criteria: ViewSection.FullString
                    section.delegate: RowLayout {
                        width: ListView.view.width
                        required property string section
                        Label {
                            text: section
                                ? serversListView.model.chaintips > 1
                                    ? qsTr('Connected @%1').arg(section)
                                    : qsTr('Connected')
                                : qsTr('Other known servers')
                            Layout.alignment: Qt.AlignLeft
                            Layout.topMargin: constants.paddingXSmall
                            Layout.leftMargin: constants.paddingSmall
                            font.pixelSize: constants.fontSizeMedium
                            color: Material.accentColor
                        }
                    }

                }
            }
        }
    }

    Component.onCompleted: {
        root.auto_connect = Config.autoConnectDefined ? Config.autoConnect : false
        root.address = Network.server
        // TODO: initial setup should not connect already, is Network.server defined?
    }
}
