import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

Pane {
    id: root
    signal next
    signal finish
    signal prev
    signal accept
    property var wizard_data : ({})
    property bool valid
    property bool last: false
    property string wizard_title: ''
    property string title: ''
    property bool securePage: false

    leftPadding: constants.paddingXLarge
    rightPadding: constants.paddingXLarge

    background: Rectangle {
        color: Material.dialogColor
        TapHandler {
            onTapped: root.forceActiveFocus()
        }
    }

    onAccept: {
        apply()
    }

    // override this in descendants to put data from the view in wizard_data
    function apply() { }

    function checkIsLast() {
        apply()
        last = wizard.wiz.isLast(wizard_data)
    }

    Component.onCompleted: {
        // NOTE: Use Qt.callLater to execute checkIsLast(), and by extension apply(),
        // otherwise Component.onCompleted handler in descendants is processed
        // _after_ apply() is called, which may lead to setting the wrong
        // wizard_data keys if apply() depends on variables set in descendant
        // Component.onCompleted handler.
        Qt.callLater(checkIsLast)

        // move focus to root of WizardComponent, otherwise Android back button
        // might be missed in Wizard root Item.
        root.forceActiveFocus()
    }

}
