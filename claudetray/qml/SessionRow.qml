import QtQuick
import "util.js" as U

Rectangle {
    id: row
    property var s            // datos de la sesion (roles del modelo)
    property double now: Date.now()
    property bool expanded: false

    width: parent ? parent.width : 300
    height: body.implicitHeight + 20
    radius: 14
    color: ma.containsMouse || expanded ? T.fillHover : T.fill
    border.width: s.state === "waiting" ? 1 : 0
    border.color: "#66FF9F0A"
    Behavior on color { ColorAnimation { duration: 150 } }
    Behavior on height { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
    clip: true

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: row.expanded = !row.expanded
    }

    Column {
        id: body
        x: 12; y: 10
        width: parent.width - 24
        spacing: 3

        Item {
            width: parent.width
            height: Math.max(proj.implicitHeight, 16)
            StatusDot { id: dot; status: s.state; anchors.verticalCenter: parent.verticalCenter; width: 8; height: 8 }
            Text {
                id: proj
                anchors { left: dot.right; leftMargin: 9; verticalCenter: parent.verticalCenter }
                text: s.project
                color: T.text
                font.pixelSize: 14; font.weight: Font.DemiBold
                width: Math.min(implicitWidth, parent.width - meta.width - 40)
                elide: Text.ElideRight
            }
            Text {
                anchors { left: proj.right; leftMargin: 6; right: meta.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
                text: s.title && s.title !== s.project ? s.title : ""
                color: T.text3
                font.pixelSize: 12
                elide: Text.ElideRight
            }
            Text {
                id: meta
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                text: U.ago(s.updated, row.now)
                color: T.text3
                font.pixelSize: 11
            }
        }

        Text {
            x: 17
            width: parent.width - 17
            text: s.activity || U.stateLabel(s.state)
            color: s.state === "waiting" ? "#FF9F0A" : T.text2
            font.pixelSize: 12
            font.family: s.activity && s.activity.indexOf("$ ") === 0 ? MONO : Qt.application.font.family
            elide: Text.ElideRight
            maximumLineCount: 1
        }

        Row {
            x: 17
            spacing: 6
            visible: s.ctx >= 0 || !!s.modelName
            topPadding: 3
            Chip { visible: !!s.modelName; text: s.modelName }
            Chip { visible: s.ctx >= 0; text: "contexto " + s.ctx + " %"; warn: s.ctx >= 80 }
            Chip { visible: s.cost > 0; text: "$" + s.cost.toFixed(2) }
        }

        Column {
            x: 17
            width: parent.width - 17
            spacing: 8
            visible: row.expanded
            topPadding: 8

            Text {
                visible: !!s.prompt
                width: parent.width
                text: "<b>Tú</b>  " + esc(s.prompt)
                textFormat: Text.StyledText
                color: T.text2; font.pixelSize: 12
                wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight
            }
            Text {
                visible: !!s.message
                width: parent.width
                text: "<b>Claude</b>  " + esc(s.message)
                textFormat: Text.StyledText
                color: T.text2; font.pixelSize: 12
                wrapMode: Text.Wrap; maximumLineCount: 5; elide: Text.ElideRight
            }
            Text {
                width: parent.width
                text: s.cwd
                color: T.text3; font.pixelSize: 11; font.family: MONO
                elide: Text.ElideMiddle
            }
            // --- escribirle a la sesion (solo Konsole)
            Column {
                id: msgBox
                property var canSend: null          // se consulta una vez al expandir
                property string feedback: ""
                visible: canSend === true
                width: parent.width
                spacing: 6
                Connections {
                    target: row
                    function onExpandedChanged() { if (row.expanded && msgBox.canSend === null) msgBox.canSend = ctrl.canMessage(s.sid) }
                }
                function send(text) {
                    var ok = ctrl.sendToSession(s.sid, text)
                    feedback = ok ? "Enviado ✓" : "No se pudo enviar"
                    if (ok) msgInput.text = ""
                    clearFeedback.restart()
                }
                Timer { id: clearFeedback; interval: 2500; onTriggered: msgBox.feedback = "" }
                Flow {
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: ["Sí, continúa", "No", "Resume lo que hiciste"]
                        Rectangle {
                            width: quick.implicitWidth + 16; height: 24; radius: 12
                            color: quickMa.pressed ? T.fillPress : quickMa.containsMouse ? T.fillHover : T.fill
                            border.width: 1; border.color: T.stroke
                            Text { id: quick; anchors.centerIn: parent; text: modelData; color: T.text; font.pixelSize: 12 }
                            MouseArea { id: quickMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: msgBox.send(modelData) }
                        }
                    }
                }
                Item {
                    width: parent.width; height: 30
                    Rectangle {
                        anchors { left: parent.left; right: sendBtn.left; rightMargin: 6; verticalCenter: parent.verticalCenter }
                        height: 30; radius: 9
                        color: T.code
                        border.width: 1; border.color: msgInput.activeFocus ? "#D97757" : T.stroke
                        TextInput {
                            id: msgInput
                            anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                            verticalAlignment: TextInput.AlignVCenter
                            color: T.text; font.pixelSize: 13
                            selectByMouse: true; clip: true
                            onAccepted: if (text.trim() !== "") msgBox.send(text)
                        }
                        Text {
                            visible: msgInput.text === ""
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: "Escribir a esta sesión…"
                            color: T.text3; font.pixelSize: 13
                        }
                    }
                    Btn {
                        id: sendBtn
                        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                        kind: "accent"; text: "Enviar"
                        enabled: msgInput.text.trim() !== ""
                        opacity: enabled ? 1 : 0.4
                        onClicked: msgBox.send(msgInput.text)
                    }
                }
                Text {
                    visible: msgBox.feedback !== ""
                    text: msgBox.feedback
                    color: msgBox.feedback.indexOf("✓") >= 0 ? "#30D158" : "#FF9F0A"
                    font.pixelSize: 11
                }
            }
            Btn {
                visible: s.pid > 0
                text: "Ir a la terminal"
                onClicked: ctrl.focusSession(s.sid)
            }
        }
    }

    function esc(t) {
        return (t || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n+/g, " ");
    }
}
