import QtQuick
import "util.js" as U

// Notificacion flotante. mode: "permission" | "info".
// bubble: burbuja sobre el icono de la bandeja (con pico) en vez de la esquina superior.
Window {
    id: w
    property var item
    property string mode: "permission"
    property bool closing: false
    property bool hiddenByStack: false
    property int targetX: 0
    property int targetY: 0
    property bool bubble: false
    property int tailDir: 1          // 1 = pico hacia abajo (bandeja abajo), -1 = hacia arriba
    property real tailX: width / 2   // en coordenadas de la ventana
    property bool showTail: false    // solo la burbuja mas cercana al icono
    property real slide: 48
    property double now: Date.now()
    readonly property int m: 22
    readonly property int tailSize: 10

    // las preguntas tienen un campo de texto: esa notificacion si puede tomar el foco
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
           | (mode === "question" ? 0 : Qt.WindowDoesNotAcceptFocus)
    color: "transparent"
    width: 372 + 2 * m
    height: card.height + 2 * m + (bubble ? tailSize : 0)
    // La esquina entra deslizando desde la derecha; la burbuja sube desde el icono.
    property real stackY: targetY
    Behavior on stackY { enabled: !w.closing; NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
    x: targetX + (bubble ? 0 : slide)
    y: stackY + (bubble ? slide * 0.4 * tailDir : 0)
    opacity: 0

    Timer { interval: 1000; running: true; repeat: true; onTriggered: w.now = Date.now() }

    Component.onCompleted: enter.start()
    ParallelAnimation {
        id: enter
        NumberAnimation { target: w; property: "slide"; to: 0; duration: w.bubble ? 360 : 420; easing.type: Easing.OutBack; easing.overshoot: w.bubble ? 1.2 : 0.8 }
        NumberAnimation { target: w; property: "opacity"; to: w.hiddenByStack ? 0 : 1; duration: 240 }
    }
    onHiddenByStackChanged: if (!closing && !enter.running) opacity = hiddenByStack ? 0 : 1
    onClosingChanged: if (closing) { enter.stop(); exit.start() }
    SequentialAnimation {
        id: exit
        ParallelAnimation {
            NumberAnimation { target: w; property: "slide"; to: w.bubble ? 30 : 64; duration: 220; easing.type: Easing.InCubic }
            NumberAnimation { target: w; property: "opacity"; to: 0; duration: 200 }
        }
        ScriptAction { script: ctrl.toastGone(w.item.id) }
    }

    function syncBlur() {
        ctrl.setBlur(w, card.x, card.y, card.width, card.height, card.radius,
                     card.tailX, card.tailSize, card.tail)
    }
    onVisibleChanged: if (visible) syncBlur()
    onHeightChanged: syncBlur()
    onTailXChanged: syncBlur()
    onShowTailChanged: syncBlur()
    onBubbleChanged: syncBlur()

    Glass {
        id: card
        x: w.m
        y: w.m + (w.bubble && w.tailDir === -1 ? w.tailSize : 0)
        width: w.width - 2 * w.m
        height: (w.mode === "permission" ? approval.implicitHeight
                 : w.mode === "question" ? question.implicitHeight : info.implicitHeight) + 28
        strong: true
        tail: w.bubble && w.showTail ? w.tailDir : 0
        tailX: w.tailX - x
        tailSize: w.tailSize

        QuestionCard {
            id: question
            visible: w.mode === "question"
            x: 16; y: 14
            width: parent.width - 32
            item: w.mode === "question" ? w.item : null
            now: w.now
            onWantsFocus: w.requestActivate()
        }

        ApprovalCard {
            id: approval
            visible: w.mode === "permission"
            x: 16; y: 14
            width: parent.width - 32
            item: w.mode === "permission" ? w.item : null
            now: w.now
        }

        Column {
            id: info
            visible: w.mode === "info"
            x: 16; y: 14
            width: parent.width - 32
            spacing: 4
            Item {
                width: parent.width; height: 18
                Glyph { id: ig; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter }
                Text {
                    anchors { left: ig.right; leftMargin: 7; verticalCenter: parent.verticalCenter }
                    text: "CLAUDE CODE"
                    color: T.text2; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 0.4
                }
                Text { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; text: "ahora"; color: T.text3; font.pixelSize: 11 }
            }
            Row {
                spacing: 7
                topPadding: 4
                StatusDot { status: w.item && w.item.kind === "done" ? "done" : "waiting"; width: 8; height: 8; anchors.verticalCenter: parent.verticalCenter }
                Text {
                    text: w.item ? w.item.title : ""; color: T.text; font.pixelSize: 14; font.weight: Font.DemiBold
                    width: Math.min(implicitWidth, info.width - 16); elide: Text.ElideRight
                }
            }
            Text {
                visible: text !== ""
                width: parent.width
                text: w.item ? w.item.body : ""
                color: T.text2; font.pixelSize: 13
                wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight
            }
        }

        MouseArea {           // los avisos se cierran solos; clic = ir a la terminal
            anchors.fill: parent
            enabled: w.mode === "info"
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: { ctrl.focusSession(w.item.sid); w.closing = true }
        }
        Timer {
            running: w.mode === "info" && !w.closing && !hover.hovered   // no se cierra mientras lo miras
            interval: 6500
            onTriggered: w.closing = true
        }
    }

    // --- cerrar (X), visible al pasar el mouse
    Item {
        anchors.fill: parent
        HoverHandler { id: hover }
    }
    Rectangle {
        id: closeBtn
        x: card.x - 7; y: card.y - 7
        width: 22; height: 22; radius: 11
        opacity: hover.hovered && !w.closing ? 1 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 140 } }
        color: closeMa.containsMouse ? (T.dark ? "#F23A3A3C" : "#F2E5E5EA") : (T.dark ? "#F22C2C2E" : "#F2F2F2F7")
        border.width: 1; border.color: T.stroke
        Repeater {
            model: [45, -45]
            Rectangle {
                anchors.centerIn: parent
                width: 9; height: 1.8; radius: 1
                rotation: modelData
                color: closeMa.containsMouse ? T.text : T.text2
            }
        }
        MouseArea {
            id: closeMa
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: ctrl.dismissToast(w.item.id)
        }
    }
}
