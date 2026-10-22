import QtQuick

Rectangle {
    property alias text: t.text
    property bool warn: false
    implicitWidth: t.implicitWidth + 12
    implicitHeight: 18
    radius: 6
    color: warn ? "#33FF9F0A" : T.fill
    Text {
        id: t
        anchors.centerIn: parent
        color: warn ? "#FF9F0A" : T.text2
        font.pixelSize: 11
        font.weight: Font.Medium
    }
}
