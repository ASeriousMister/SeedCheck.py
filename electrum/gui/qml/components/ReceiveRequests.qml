import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQml.Models
import QtQml

import org.electrum 1.0

import "controls"

Pane {
    id: root
    objectName: 'ReceiveRequests'

    padding: 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: constants.paddingLarge

            InfoTextArea {
                Layout.fillWidth: true
                Layout.bottomMargin: constants.paddingLarge
                visible: !Config.userKnowsPressAndHold
                text: qsTr('To access this list from the main screen, press and hold the Receive button')
            }

            Heading {
                text: qsTr('Pending requests')
            }

            Frame {
                background: PaneInsetBackground {}

                verticalPadding: 0
                horizontalPadding: 0
                Layout.fillHeight: true
                Layout.fillWidth: true

                ElListView {
                    id: listview
                    anchors.fill: parent
                    clip: true
                    currentIndex: -1

                    model: DelegateModel {
                        id: delegateModel
                        model: Daemon.currentWallet.requestModel
                        delegate: InvoiceDelegate {
                            onClicked: {
                                app.stack.getRoot().openRequest(model.key)
                                listview.currentIndex = -1
                            }
                            onPressAndHold: listview.currentIndex = index
                        }
                    }

                    add: Transition {
                        NumberAnimation { properties: 'scale'; from: 0.75; to: 1; duration: 500 }
                        NumberAnimation { properties: 'opacity'; from: 0; to: 1; duration: 500 }
                    }
                    addDisplaced: Transition {
                        SpringAnimation { properties: 'y'; duration: 200; spring: 5; damping: 0.5; mass: 2 }
                    }

                    remove: Transition {
                        NumberAnimation { properties: 'scale'; to: 0.75; duration: 300 }
                        NumberAnimation { properties: 'opacity'; to: 0; duration: 300 }
                    }
                    removeDisplaced: Transition {
                        SequentialAnimation {
                            PauseAnimation { duration: 200 }
                            SpringAnimation { properties: 'y'; duration: 100; spring: 5; damping: 0.5; mass: 2 }
                        }
                    }

                    ScrollIndicator.vertical: ScrollIndicator { }
                }
            }
        }

        ButtonContainer {
            Layout.fillWidth: true
            FlatButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: qsTr('Delete')
                icon.source: '../../icons/delete.png'
                visible: listview.currentIndex >= 0
                onClicked: {
                    Daemon.currentWallet.deleteRequest(listview.currentItem.getKey())
                }
            }
            FlatButton {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: qsTr('View')
                icon.source: '../../icons/tab_receive.png'
                visible: listview.currentIndex >= 0
                onClicked: {
                    app.stack.getRoot().openRequest(listview.currentItem.getKey())
                }
            }
        }
    }
}
