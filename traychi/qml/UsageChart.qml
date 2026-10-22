import QtQuick
import "util.js" as U

// Consumo por dia (tokens) de los ultimos 7 o 30 dias, leido de los registros locales.
Column {
    id: uc
    property int days: 7
    property bool asTable: false
    property int hovered: -1
    spacing: 12

    readonly property var rows: { ctrl.dailyRevision; return ctrl.usageSeries(uc.days) }
    readonly property var sum: { ctrl.dailyRevision; return ctrl.usageSummary(uc.days) }
    // escala con pasos redondos (1, 2, 2,5 o 5 × 10^n), calculada de una vez y con tope:
    // si "ticks" dependiera de "step" por separado, al iniciar podia valer NaN y el Repeater no terminaba
    readonly property var scale: {
        var m = 0
        for (var i = 0; i < rows.length; i++) m = Math.max(m, rows[i].total || 0)
        var st = niceStep(Math.max(m, 1) / 4)
        var n = Math.ceil(m / st)
        n = isFinite(n) ? Math.min(6, Math.max(1, n)) : 1
        return { step: st, ticks: n, max: st * n }
    }
    readonly property real step: scale.step
    readonly property int ticks: scale.ticks
    readonly property real maxTotal: scale.max

    function niceStep(v) {
        if (!(v > 0) || !isFinite(v)) return 1
        var p = Math.pow(10, Math.floor(Math.log(v) / Math.LN10)), n = v / p
        return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p
    }
    function fmt(v) {
        if (v >= 1e6) return (+(v / 1e6).toFixed(v >= 1e7 ? 0 : 1)).toString().replace(".", ",") + " M"
        if (v >= 1e3) return Math.round(v / 1e3) + " k"
        return "" + Math.round(v)
    }
    function dayLabel(iso, long) {
        var d = new Date(iso + "T12:00:00")
        return long ? U.DAYS[d.getDay()] + " " + d.getDate() : "" + d.getDate()
    }

    // --- titulo y rango
    Item {
        width: parent.width; height: 28
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            anchors.verticalCenter: parent.verticalCenter
            leftPadding: 2
            text: "Tokens por día"
            color: T.text2; font.pixelSize: 12
        }
        Rectangle {
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            width: rangeRow.implicitWidth + 4; height: 26; radius: 8
            color: T.fill; border.width: 1; border.color: T.stroke
            Row {
                id: rangeRow
                x: 2; anchors.verticalCenter: parent.verticalCenter
                Repeater {
                    model: [7, 30]
                    Rectangle {
                        width: rl.implicitWidth + 18; height: 22; radius: 6
                        color: uc.days === modelData ? T.fillPress : "transparent"
                        Text {
                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                            id: rl; anchors.centerIn: parent
                            text: modelData + " días"
                            color: uc.days === modelData ? T.text : T.text2
                            font.pixelSize: 12; font.weight: uc.days === modelData ? Font.DemiBold : Font.Normal
                        }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { uc.days = modelData; uc.hovered = -1 } }
                    }
                }
            }
        }
    }

    // --- resumen
    Row {
        width: parent.width
        spacing: 8
        Repeater {
            model: [
                { label: "Total", value: uc.fmt(uc.sum.total || 0) },
                { label: "Promedio diario", value: uc.fmt(uc.sum.avg || 0) },
                { label: "Hoy", value: uc.fmt(uc.sum.today || 0)
                    + (uc.sum.ratio >= 1.15 || (uc.sum.ratio > 0 && uc.sum.ratio <= 0.85)
                       ? "  " + uc.sum.ratio.toFixed(1).replace(".", ",") + "×" : "") }
            ]
            Rectangle {
                width: (uc.width - 16) / 3; height: 52; radius: 12
                color: T.fill
                Column {
                    x: 10; anchors.verticalCenter: parent.verticalCenter
                    spacing: 2
                    Text { textFormat: Text.PlainText; text: modelData.label; color: T.text3; font.pixelSize: 11 }
                    Text { textFormat: Text.PlainText; text: modelData.value; color: T.text; font.pixelSize: 15; font.weight: Font.DemiBold; font.features: { "tnum": 1 } }
                }
            }
        }
    }

    // --- grafico de barras
    Item {
        id: chart
        visible: !uc.asTable
        width: parent.width
        height: 160
        readonly property real axisW: 40
        readonly property real plotH: height - 20
        readonly property real slot: (width - axisW) / Math.max(1, uc.rows.length)
        readonly property real gap: uc.days === 7 ? 8 : 2

        // lineas guia (recesivas) con etiquetas
        Repeater {
            model: uc.ticks
            Item {
                readonly property real v: uc.step * (index + 1)
                y: chart.plotH - chart.plotH * (index + 1) / uc.ticks
                width: chart.width; height: 1
                Rectangle { x: chart.axisW; width: chart.width - chart.axisW; height: 1; color: T.fill }
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    anchors { right: parent.left; rightMargin: -chart.axisW + 6; verticalCenter: parent.verticalCenter }
                    text: uc.fmt(v); color: T.text3; font.pixelSize: 10
                }
            }
        }
        Rectangle { x: chart.axisW; y: chart.plotH; width: chart.width - chart.axisW; height: 1; color: T.stroke }

        Repeater {
            model: uc.rows
            Item {
                readonly property bool isToday: index === uc.rows.length - 1
                x: chart.axisW + index * chart.slot
                width: chart.slot; height: chart.height
                Item {                // recorte en la linea base: extremo superior redondeado, base recta
                    width: parent.width; height: chart.plotH
                    clip: true
                    Rectangle {
                        readonly property real h: modelData.total > 0 ? Math.max(3, chart.plotH * modelData.total / uc.maxTotal) : 0
                        x: chart.gap / 2; width: parent.width - chart.gap
                        y: chart.plotH - h; height: h + 6
                        radius: Math.min(4, width / 2)
                        color: "#D97757"
                        opacity: uc.hovered === -1 ? (isToday ? 1 : 0.75) : (uc.hovered === index ? 1 : 0.4)
                        Behavior on y { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                        Behavior on opacity { NumberAnimation { duration: 120 } }
                    }
                }
                Text { textFormat: Text.PlainText;                // etiquetas del eje x (todas en 7 dias, una de cada 5 en 30)
                    visible: uc.days === 7 || index % 5 === (uc.rows.length - 1) % 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: chart.plotH + 5
                    text: isToday ? "hoy" : uc.dayLabel(modelData.date, uc.days === 7)
                    color: isToday ? T.text2 : T.text3; font.pixelSize: 10
                }
                MouseArea {           // zona de hover mas grande que la barra
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: uc.hovered = index
                    onExited: if (uc.hovered === index) uc.hovered = -1
                }
            }
        }

        // tooltip
        Rectangle {
            id: tip
            readonly property var r: uc.hovered >= 0 ? uc.rows[uc.hovered] : null
            visible: r !== null
            width: tipCol.implicitWidth + 20; height: tipCol.implicitHeight + 16
            radius: 10
            color: T.dark ? "#F22C2C2E" : "#F2FFFFFF"
            border.width: 1; border.color: T.stroke
            x: Math.max(0, Math.min(chart.width - width, chart.axisW + (uc.hovered + 0.5) * chart.slot - width / 2))
            y: 0
            z: 10
            Column {
                id: tipCol
                x: 10; y: 8
                spacing: 2
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    text: tip.r ? uc.dayLabel(tip.r.date, true) + " · " + uc.fmt(tip.r.total) + " tokens" : ""
                    color: T.text; font.pixelSize: 12; font.weight: Font.DemiBold
                }
                Text { textFormat: Text.PlainText; text: tip.r ? "Entrada " + uc.fmt(tip.r.input) + "  ·  salida " + uc.fmt(tip.r.output) : ""; color: T.text2; font.pixelSize: 11 }
                Text { textFormat: Text.PlainText; text: tip.r ? "Caché: escrito " + uc.fmt(tip.r.cache_write) + "  ·  leído " + uc.fmt(tip.r.cache_read) : ""; color: T.text2; font.pixelSize: 11 }
                Text { textFormat: Text.PlainText; text: tip.r ? tip.r.messages + " respuestas" : ""; color: T.text3; font.pixelSize: 11 }
            }
        }
    }

    // --- tabla (alternativa accesible al grafico)
    Column {
        visible: uc.asTable
        width: parent.width
        spacing: 2
        Repeater {
            model: uc.asTable ? uc.rows.slice().reverse() : []
            Item {
                width: uc.width; height: 22
                Text { textFormat: Text.PlainText; text: uc.dayLabel(modelData.date, true) + (index === 0 ? " (hoy)" : ""); color: T.text2; font.pixelSize: 12 }
                Text { textFormat: Text.PlainText; anchors.right: parent.right; text: uc.fmt(modelData.total) + "  ·  " + modelData.messages + " resp."; color: T.text; font.pixelSize: 12; font.features: { "tnum": 1 } }
            }
        }
    }

    Item {
        width: parent.width; height: 20
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            anchors.verticalCenter: parent.verticalCenter
            text: "Entrada + salida + caché escrita · registros locales"
            color: T.text3; font.pixelSize: 10
            width: parent.width - toggle.width - 8; elide: Text.ElideRight
        }
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            id: toggle
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            text: uc.asTable ? "Ver gráfico" : "Ver tabla"
            color: "#F0A585"; font.pixelSize: 11
            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: uc.asTable = !uc.asTable }
        }
    }
}
