import QtQuick
import "util.js" as U

Column {
    id: u
    property string label
    property real pct: -1
    property real resets: 0
    property double now: Date.now()
    spacing: 6

    Item {
        width: parent.width
        height: name.implicitHeight
        Text { id: name; text: u.label; color: T.text; font.pixelSize: 13; font.weight: Font.Medium }
        Text {
            anchors.right: parent.right
            text: u.pct < 0 ? "—" : Math.round(u.pct) + " %"
            color: u.pct >= 70 ? U.levelColor(u.pct) : T.text
            font.pixelSize: 13; font.weight: Font.DemiBold
            font.features: { "tnum": 1 }
        }
    }

    Rectangle {
        width: parent.width; height: 6; radius: 3
        color: T.fill
        Rectangle {
            height: parent.height; radius: 3
            width: Math.max(u.pct > 0 ? height : 0, parent.width * Math.min(100, Math.max(0, u.pct)) / 100)
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Qt.lighter(U.levelColor(u.pct), 1.25) }
                GradientStop { position: 1; color: U.levelColor(u.pct) }
            }
            Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
        }
    }

    Text {
        text: u.pct < 0 ? "Sin datos todavía"
            : u.resets > 0 ? "Se reinicia " + U.until(u.resets, u.now) : "Ventana reiniciada"
        color: T.text3
        font.pixelSize: 11
    }
}
