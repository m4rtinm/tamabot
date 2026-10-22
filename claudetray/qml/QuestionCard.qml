import QtQuick
import "util.js" as U

// Pregunta con opciones (AskUserQuestion): elegir y enviar sin ir a la terminal.
Column {
    id: qc
    property var item
    property bool compact: false
    property double now: Date.now()
    signal wantsFocus()             // la notificacion necesita foco para escribir
    spacing: 12

    readonly property var questions: item && item.questions ? item.questions : []
    property var sel: []            // por pregunta: etiquetas elegidas
    property var other: []          // por pregunta: texto libre
    property string forId: ""
    onQuestionsChanged: {           // solo se reinicia al cambiar de pregunta, no al refrescar la lista
        if (!item || item.id === forId) return
        forId = item.id
        sel = questions.map(function () { return [] })
        other = questions.map(function () { return "" })
    }

    readonly property real remaining: item ? Math.max(0, 1 - (now - item.created) / (item.timeout * 1000)) : 1
    readonly property bool complete: {
        if (!questions.length) return false
        for (var i = 0; i < questions.length; i++)
            if (!((sel[i] && sel[i].length) || (other[i] && other[i].trim() !== ""))) return false
        return true
    }

    function toggle(qi, label, multi) {
        var s = sel.slice(), cur = (s[qi] || []).slice(), at = cur.indexOf(label)
        if (multi) { if (at >= 0) cur.splice(at, 1); else cur.push(label) }
        else {
            cur = at >= 0 ? [] : [label]
            var o = other.slice(); o[qi] = ""; other = o      // en seleccion unica, elegir borra el texto libre
        }
        s[qi] = cur; sel = s
    }
    function setOther(qi, text) {
        var o = other.slice(); o[qi] = text; other = o
        if (text !== "" && !questions[qi].multiSelect) { var s = sel.slice(); s[qi] = []; sel = s }
    }
    function submit() {
        var answers = {}
        for (var i = 0; i < questions.length; i++) {
            var parts = (sel[i] || []).slice()
            if (other[i] && other[i].trim() !== "") parts.push(other[i].trim())
            answers[questions[i].question] = parts.join(", ")
        }
        ctrl.answerQuestion(item.id, answers)
    }

    Item {
        width: parent.width
        height: 18
        Glyph { id: g; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter; visible: !qc.compact }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            anchors { left: qc.compact ? parent.left : g.right; leftMargin: qc.compact ? 0 : 7; verticalCenter: parent.verticalCenter }
            width: parent.width - (qc.compact ? 0 : 23) - ago.implicitWidth - 8
            elide: Text.ElideRight
            text: (qc.compact ? "" : "CLAUDE CODE  ·  ") + (item ? item.project : "")
            color: T.text2
            font.pixelSize: 11; font.weight: Font.DemiBold
            font.letterSpacing: qc.compact ? 0 : 0.4
        }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            id: ago
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            text: item ? U.ago(item.created, qc.now) : ""
            color: T.text3; font.pixelSize: 11
        }
    }

    Repeater {
        model: qc.questions
        Column {
            id: qBlock
            readonly property int qi: index
            readonly property bool multi: !!modelData.multiSelect
            width: qc.width
            spacing: 6

            Row {
                spacing: 6
                Chip { visible: !!modelData.header; text: modelData.header || "" }
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    visible: qBlock.multi
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Puedes elegir varias"
                    color: T.text3; font.pixelSize: 11
                }
            }
            Text {
                textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                width: parent.width
                text: modelData.question
                color: T.text
                font.pixelSize: 14; font.weight: Font.DemiBold
                wrapMode: Text.Wrap
            }
            Repeater {
                model: modelData.options || []
                Rectangle {
                    id: opt
                    readonly property bool picked: (qc.sel[qBlock.qi] || []).indexOf(modelData.label) >= 0
                    width: qBlock.width
                    height: optCol.implicitHeight + 14
                    radius: 10
                    color: picked ? "#26D97757" : optMa.containsMouse ? T.fillHover : T.fill
                    border.width: 1
                    border.color: picked ? "#99D97757" : T.stroke
                    Behavior on color { ColorAnimation { duration: 120 } }

                    Rectangle {      // radio (unica) o casilla (varias)
                        x: 10; y: 9
                        width: 16; height: 16
                        radius: qBlock.multi ? 4 : 8
                        color: opt.picked ? "#D97757" : "transparent"
                        border.width: opt.picked ? 0 : 1.5
                        border.color: T.text3
                        Rectangle {
                            visible: opt.picked && !qBlock.multi
                            anchors.centerIn: parent
                            width: 6; height: 6; radius: 3; color: "white"
                        }
                        Text {
                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                            visible: opt.picked && qBlock.multi
                            anchors.centerIn: parent
                            text: "✓"; color: "white"; font.pixelSize: 11; font.bold: true
                        }
                    }
                    Column {
                        id: optCol
                        x: 34; y: 7
                        width: parent.width - 44
                        spacing: 1
                        Text {
                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                            width: parent.width
                            text: modelData.label
                            color: T.text; font.pixelSize: 13; font.weight: Font.Medium
                            wrapMode: Text.Wrap
                        }
                        Text {
                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                            visible: !!modelData.description
                            width: parent.width
                            text: modelData.description || ""
                            color: T.text2; font.pixelSize: 11
                            wrapMode: Text.Wrap
                            maximumLineCount: 3; elide: Text.ElideRight
                        }
                    }
                    MouseArea {
                        id: optMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: qc.toggle(qBlock.qi, modelData.label, qBlock.multi)
                    }
                }
            }
            Rectangle {              // otra respuesta (texto libre)
                width: parent.width; height: 32; radius: 10
                color: T.code
                border.width: 1
                border.color: otherInput.activeFocus ? "#D97757" : T.stroke
                TextInput {
                    id: otherInput
                    anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                    verticalAlignment: TextInput.AlignVCenter
                    color: T.text; font.pixelSize: 13
                    selectByMouse: true
                    clip: true
                    text: qc.other[qBlock.qi] || ""
                    onTextEdited: qc.setOther(qBlock.qi, text)
                    onAccepted: if (qc.complete) qc.submit()
                    onActiveFocusChanged: if (activeFocus) qc.wantsFocus()
                }
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    visible: otherInput.text === ""
                    anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                    text: "Otra respuesta…"
                    color: T.text3; font.pixelSize: 13
                }
                MouseArea {          // en la notificacion hay que pedir foco antes de escribir
                    anchors.fill: parent
                    enabled: !otherInput.activeFocus
                    cursorShape: Qt.IBeamCursor
                    onClicked: { qc.wantsFocus(); otherInput.forceActiveFocus() }
                }
            }
        }
    }

    Item {
        width: parent.width
        height: 28
        Btn {
            anchors.verticalCenter: parent.verticalCenter
            kind: "quiet"; text: "Terminal"
            onClicked: ctrl.toTerminal(item.id)
        }
        Btn {
            anchors.right: parent.right
            kind: "accent"; text: "Responder"
            enabled: qc.complete
            opacity: qc.complete ? 1 : 0.4
            onClicked: qc.submit()
        }
    }

    Rectangle {          // tiempo que queda antes de devolverla a la terminal
        x: 2
        width: parent.width - 4; height: 2; radius: 1
        color: "transparent"
        visible: !qc.compact
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * qc.remaining; height: 2; radius: 1
            color: qc.remaining < 0.15 ? "#FF9F0A" : T.fillPress
            Behavior on width { NumberAnimation { duration: 1000 } }
        }
    }
}
