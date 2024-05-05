import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

import org.electrum 1.0

import "../controls"

WizardComponent {
    securePage: true

    valid: seedtext.text != '' && extendcb.checked ? customwordstext.text != '' : true

    function apply() {
        wizard_data['seed'] = seedtext.text
        wizard_data['seed_variant'] = 'electrum' // generated seed always electrum variant
        wizard_data['seed_extend'] = extendcb.checked
        wizard_data['seed_extra_words'] = extendcb.checked ? customwordstext.text : ''
    }

    function setWarningText(numwords) {
        var t = [
            '<p>',
            qsTr('Please save these %1 words on paper (order is important).').arg(numwords),
            qsTr('This seed will allow you to recover your wallet in case of computer failure.'),
            '</p>',
            '<b>' + qsTr('WARNING') + ':</b>',
            '<ul>',
            '<li>' + qsTr('Never disclose your seed.') + '</li>',
            '<li>' + qsTr('Never type it on a website.') + '</li>',
            '<li>' + qsTr('Do not store it electronically.') + '</li>',
            '</ul>'
        ]
        warningtext.text = t.join(' ')
    }

    Flickable {
        anchors.fill: parent
        contentHeight: mainLayout.height
        clip:true
        interactive: height < contentHeight

        GridLayout {
            id: mainLayout
            width: parent.width
            columns: 1

            InfoTextArea {
                id: warningtext
                Layout.fillWidth: true
                iconStyle: InfoTextArea.IconStyle.Warn
            }

            Label {
                Layout.topMargin: constants.paddingMedium
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: qsTr('Your wallet generation seed is:')
            }

            SeedTextArea {
                id: seedtext
                readOnly: true
                Layout.fillWidth: true

                BusyIndicator {
                    anchors.centerIn: parent
                    height: parent.height * 2/3
                    visible: seedtext.text == ''
                }
            }

            ElCheckBox {
                id: extendcb
                Layout.fillWidth: true
                text: qsTr('Extend seed with custom words')
            }

            TextField {
                id: customwordstext
                visible: extendcb.checked
                Layout.fillWidth: true
                placeholderText: qsTr('Enter your custom word(s)')
                inputMethodHints: Qt.ImhNoPredictiveText
            }

            Component.onCompleted : {
                setWarningText(12)
            }
        }
    }

    Component.onCompleted: {
        bitcoin.generateSeed(wizard_data['seed_type'])
    }

    Bitcoin {
        id: bitcoin
        onGeneratedSeedChanged: {
            seedtext.text = generatedSeed
            setWarningText(generatedSeed.split(' ').length)
        }
    }
}
