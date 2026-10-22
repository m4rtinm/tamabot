import QtQuick
import "util.js" as U

// Solicitud de permiso: que quiere hacer Claude y los botones para decidir.
Column {
    id: card
    property var item
    property bool compact: false     // dentro del panel (sin cabecera de app)
    property double now: Date.now()
    spacing: 10

    readonly property real remaining: item ? Math.max(0, 1 - (now - item.created) / (item.timeout * 1000)) : 1

    Item {
        width: parent.width
        height: 18
        Glyph { id: g; width: 16; height: 16; anchors.verticalCenter: parent.verticalCenter; visible: !card.compact }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            anchors { left: card.compact ? parent.left : g.right; leftMargin: card.compact ? 0 : 7; verticalCenter: parent.verticalCenter }
            width: parent.width - (card.compact ? 0 : 23) - agoText.implicitWidth - 8
            elide: Text.ElideRight
            text: (card.compact ? "" : "CLAUDE CODE  ·  ") + (item ? item.project : "")
            color: T.text2
            font.pixelSize: 11; font.weight: Font.DemiBold
            font.letterSpacing: card.compact ? 0 : 0.4
        }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            id: agoText
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            text: item ? U.ago(item.created, card.now) : ""
            color: T.text3; font.pixelSize: 11
        }
    }

    Column {
        width: parent.width
        spacing: 2
        Row {
            spacing: 8
            width: parent.width
            Text {
                textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                text: item ? item.title : ""
                color: T.text
                font.pixelSize: 14; font.weight: Font.DemiBold
                width: Math.min(implicitWidth, parent.width - (dangerChip.visible ? dangerChip.width + 8 : 0))
                elide: Text.ElideRight
            }
            Rectangle {
                id: dangerChip
                visible: !!(item && item.danger)
                anchors.verticalCenter: parent.verticalCenter
                width: warn.implicitWidth + 12; height: 18; radius: 6
                color: "#33FF453A"
                Text { textFormat: Text.PlainText; id: warn; anchors.centerIn: parent; text: "Destructivo"; color: "#FF6961"; font.pixelSize: 11; font.weight: Font.DemiBold }
            }
        }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            visible: text !== ""
            width: parent.width
            text: item ? item.subtitle : ""
            color: T.text2
            font.pixelSize: 13
            elide: Text.ElideMiddle
        }
    }

    Rectangle {
        visible: !!(item && item.body !== "")
        width: parent.width
        height: Math.min(code.implicitHeight + 18, card.compact ? 110 : 190)
        radius: 10
        color: T.code
        border.width: 1
        border.color: T.stroke
        clip: true

        Flickable {
            anchors.fill: parent
            anchors.margins: 9
            contentHeight: code.implicitHeight
            contentWidth: width
            boundsBehavior: Flickable.StopAtBounds
            interactive: contentHeight > height

            Column {
                id: code
                width: parent.width
                Repeater {
                    model: item ? item.body.split("\n") : []
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        width: code.width
                        text: modelData
                        wrapMode: item.bodyKind === "text" ? Text.Wrap : Text.WrapAnywhere
                        font.family: item.bodyKind === "text" ? Qt.application.font.family : MONO
                        font.pixelSize: 12
                        color: item.bodyKind !== "diff" ? T.text
                             : modelData.indexOf("+ ") === 0 ? "#30D158"
                             : modelData.indexOf("- ") === 0 ? "#FF6961" : T.text2
                    }
                }
            }
        }
    }

    Item {
        width: parent.width
        height: 28
        Row {
            spacing: 2
            anchors.verticalCenter: parent.verticalCenter
            Btn {
                kind: "quiet"; text: "Siempre"
                visible: !!(item && item.canAlways)
                onClicked: ctrl.allowAlways(item.id)
            }
            Btn {
                kind: "quiet"; text: "Terminal"
                onClicked: ctrl.toTerminal(item.id)
            }
        }
        Row {
            anchors.right: parent.right
            spacing: 8
            Btn { text: "Rechazar"; onClicked: ctrl.deny(item.id) }
            Btn {
                kind: (item && item.danger) ? "danger" : "accent"
                hold: !!(item && item.danger)
                text: "Permitir"
                onClicked: ctrl.allow(item.id)
            }
        }
    }

    Rectangle {          // tiempo que queda antes de devolverla a la terminal
        x: 2
        width: parent.width - 4; height: 2; radius: 1
        color: "transparent"
        visible: !card.compact
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * card.remaining; height: 2; radius: 1
            color: card.remaining < 0.15 ? "#FF9F0A" : T.fillPress
            Behavior on width { NumberAnimation { duration: 1000 } }
        }
    }
}
