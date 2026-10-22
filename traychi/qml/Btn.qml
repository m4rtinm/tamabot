import QtQuick

// Boton estilo macOS. kind: "glass" | "accent" | "danger" | "quiet".
// Con hold: true hay que mantenerlo presionado (para comandos destructivos).
Rectangle {
    id: b
    property string text
    property string kind: "glass"
    property bool hold: false
    property int holdMs: 900
    property real progress: 0
    signal clicked()

    readonly property color base: kind === "accent" ? "#26A96E" : kind === "danger" ? "#FF453A" : "transparent"
    implicitHeight: 28
    implicitWidth: label.implicitWidth + (kind === "quiet" ? 12 : 26)
    radius: 9
    color: {
        if (kind === "accent" || kind === "danger") {
            if (hold) return Qt.rgba(base.r, base.g, base.b, 0.28);
            return ma.pressed ? Qt.darker(base, 1.12) : ma.containsMouse ? Qt.lighter(base, 1.08) : base;
        }
        if (kind === "quiet") return ma.pressed ? T.fillPress : ma.containsMouse ? T.fill : "transparent";
        return ma.pressed ? T.fillPress : ma.containsMouse ? T.fillHover : T.fill;
    }
    border.width: kind === "glass" ? 1 : 0
    border.color: T.stroke
    scale: ma.pressed ? 0.97 : 1
    Behavior on color { ColorAnimation { duration: 120 } }
    Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }

    Rectangle {          // relleno de "mantener presionado"
        visible: b.hold
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        width: parent.width * b.progress
        radius: b.radius
        color: b.base
    }

    Text {
        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
        id: label
        anchors.centerIn: parent
        text: b.hold && b.progress === 0 && !ma.pressed ? "Mantén: " + b.text : b.text
        font.pixelSize: 13
        font.weight: kind === "quiet" ? Font.Medium : Font.DemiBold
        color: (kind === "accent" || kind === "danger") && !b.hold ? "white"
             : kind === "quiet" ? T.text2 : T.text
    }

    NumberAnimation {
        id: fill
        target: b; property: "progress"; from: 0; to: 1
        duration: b.holdMs
        onFinished: if (b.progress >= 1) { b.clicked(); b.progress = 0 }
    }
    NumberAnimation { id: unfill; target: b; property: "progress"; to: 0; duration: 180 }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onPressed: if (b.hold) { unfill.stop(); fill.start() }
        onReleased: if (b.hold && b.progress < 1) { fill.stop(); unfill.start() }
        onClicked: if (!b.hold) b.clicked()
    }
}
