import QtQuick
import "util.js" as U

// Historial de decisiones: resumen del dia, buscador y lista.
Column {
    id: hv
    property double now: Date.now()
    property string query: ""
    spacing: 10

    readonly property var stats: ctrl.historyStats
    readonly property var rows: {
        var q = hv.query.trim().toLowerCase(), out = [];
        var all = ctrl.historyRecent;
        for (var i = 0; i < all.length && out.length < 80; i++) {
            var e = all[i];
            if (e.kind !== "decision") continue;
            if (q && ((e.project || "") + " " + (e.title || "") + " " + (e.detail || "") + " "
                      + U.outcomeLabel(e.outcome)).toLowerCase().indexOf(q) < 0) continue;
            out.push(e);
        }
        return out;
    }

    Flow {                     // resumen de hoy
        width: parent.width
        spacing: 6
        Chip { text: "Hoy: " + hv.stats.today_allowed + " permitidas" }
        Chip { text: hv.stats.today_denied + " rechazadas"; warn: hv.stats.today_denied > 0 }
        Chip { text: hv.stats.today_done + " terminadas" }
        Chip { visible: hv.stats.streak > 1; text: "racha " + hv.stats.streak + " días" }
    }

    Rectangle {                // buscador
        width: parent.width; height: 30; radius: 9
        color: T.code
        border.width: 1; border.color: search.activeFocus ? "#D97757" : T.stroke
        TextInput {
            id: search
            anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
            verticalAlignment: TextInput.AlignVCenter
            color: T.text; font.pixelSize: 13
            selectByMouse: true
            onTextChanged: hv.query = text
        }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            visible: search.text === ""
            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
            text: "Buscar por proyecto, comando o resultado…"
            color: T.text3; font.pixelSize: 13
        }
    }

    Repeater {
        model: hv.rows
        Rectangle {
            width: hv.width
            height: col.implicitHeight + 16
            radius: 12
            color: T.fill
            Rectangle {        // color del resultado
                x: 10; y: 13
                width: 7; height: 7; radius: 4
                color: U.outcomeColor(modelData.outcome)
            }
            Column {
                id: col
                x: 26; y: 8
                width: parent.width - 36
                spacing: 2
                Item {
                    width: parent.width; height: 17
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        id: ttl
                        text: (modelData.project || "") + "  ·  " + (modelData.title || modelData.tool)
                        color: T.text; font.pixelSize: 12; font.weight: Font.DemiBold
                        width: Math.min(implicitWidth, parent.width - when.width - 8)
                        elide: Text.ElideRight
                    }
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        id: when
                        anchors.right: parent.right
                        text: U.clock(modelData.ts, hv.now)
                        color: T.text3; font.pixelSize: 11
                    }
                }
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    visible: !!modelData.detail
                    width: parent.width
                    text: modelData.detail || ""
                    color: T.text2; font.pixelSize: 11; font.family: MONO
                    elide: Text.ElideRight
                }
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    text: U.outcomeLabel(modelData.outcome) + (modelData.danger ? "  ·  destructivo" : "")
                    color: U.outcomeColor(modelData.outcome); font.pixelSize: 11
                }
            }
        }
    }

    Text {
        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
        visible: hv.rows.length === 0
        width: parent.width
        topPadding: 6; bottomPadding: 6
        horizontalAlignment: Text.AlignHCenter
        text: hv.query ? "Nada coincide con la búsqueda." : "Todavía no hay decisiones registradas."
        color: T.text3; font.pixelSize: 12
    }
}
