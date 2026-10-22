import QtQuick
import QtQuick.Controls
import "util.js" as U

// Panel que se abre desde el icono de la bandeja.
Window {
    id: panel
    visible: false
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"
    title: "Traychi"

    readonly property int m: 22
    property bool autoHide: true
    property string view: "main"      // main | pet | settings | history | usage
    property int maxHeight: 680
    property bool anchorBottom: true
    property int anchorEdge: 600
    property double now: Date.now()
    readonly property var usage: ctrl.usage
    readonly property var summary: ctrl.summary

    // frase de la mascota con efecto de maquina de escribir
    readonly property string fullLine: summary.line + (ctrl.muted ? "\n" + ctrl.muteLabel : "")
    property int typed: 0
    onFullLineChanged: { typed = 0; typer.restart(); pop.restart() }
    Timer {
        id: typer
        interval: 28; repeat: true
        onTriggered: { panel.typed += 1; if (panel.typed >= panel.fullLine.length) stop() }
    }

    width: 392 + 2 * m
    height: Math.min(col.implicitHeight + 32, maxHeight) + 2 * m
    y: anchorBottom ? anchorEdge - height : anchorEdge

    Timer { interval: 1000; running: panel.visible; repeat: true; onTriggered: panel.now = Date.now() }

    onActiveChanged: if (!active && visible && autoHide) visible = false
    onVisibleChanged: if (visible) { now = Date.now(); intro.restart(); syncBlur(); typed = 0; typer.restart() }
    onHeightChanged: syncBlur()
    function syncBlur() { ctrl.setBlur(panel, m, m, card.width, card.height, card.radius, 0, 0, 0) }

    Shortcut { sequence: "Escape"; onActivated: if (panel.view !== "main") panel.view = "main"; else panel.visible = false }
    function toggleView(v) { panel.view = panel.view === v ? "main" : v }

    ParallelAnimation {
        id: intro
        NumberAnimation { target: card; property: "opacity"; from: 0; to: 1; duration: 180 }
        NumberAnimation { target: card; property: "scale"; from: 0.965; to: 1; duration: 320; easing.type: Easing.OutBack; easing.overshoot: 0.9 }
    }

    Glass {
        id: card
        anchors.fill: parent
        anchors.margins: panel.m
        radius: 22
        transformOrigin: panel.anchorBottom ? Item.Bottom : Item.Top

        Flickable {
            id: flick
            objectName: "flick"
            anchors.fill: parent
            anchors.margins: 16
            contentHeight: col.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { policy: flick.contentHeight > flick.height ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff; width: 6 }

            Column {
                id: col
                width: flick.width
                spacing: 14

                // --- cabecera: la mascota y lo que te dice
                Item {
                    width: parent.width
                    height: Math.max(84, headCol.implicitHeight + 8)
                    Pet {
                        id: petView
                        s: 76
                        anchors.verticalCenter: parent.verticalCenter
                        mood: panel.summary.mood
                        emote: panel.summary.emote
                        talking: typer.running
                        design: ctrl.pet.design || "clawd"
                        bodyColor: ctrl.pet.color
                        accessory: ctrl.pet.accessory
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: panel.toggleView("pet")
                        }
                    }
                    IconBtn {           // ajustes
                        id: gear
                        anchors { right: parent.right; top: parent.top }
                        icon: "settings"
                        active: panel.view === "settings"
                        onClicked: panel.toggleView("settings")
                    }
                    IconBtn {           // historial
                        anchors { right: bellBtn.left; rightMargin: 4; top: parent.top }
                        icon: "history"
                        active: panel.view === "history"
                        onClicked: panel.toggleView("history")
                    }
                    IconBtn {           // silenciar / reactivar
                        id: bellBtn
                        anchors { right: gear.left; rightMargin: 4; top: parent.top }
                        icon: ctrl.muted ? "bell-off" : "bell"
                        active: ctrl.muted
                        onClicked: ctrl.setMute(ctrl.muted ? 0 : -1)
                    }
                    Column {
                        id: headCol
                        anchors { left: petView.right; leftMargin: 14; right: parent.right; verticalCenter: parent.verticalCenter }
                        spacing: 6
                        Text { textFormat: Text.PlainText;                // nombre: deja libre la zona de los 3 botones
                            width: parent.width - 104
                            text: ctrl.pet.name
                            color: T.text; font.pixelSize: 16; font.weight: Font.Bold
                            elide: Text.ElideRight
                        }
                        Rectangle {           // globo de dialogo
                            id: speech
                            width: Math.min(parent.width, line.contentWidth + 22)
                            height: line.implicitHeight + 14
                            radius: 12
                            color: T.fillHover
                            border.width: 1; border.color: T.stroke
                            Rectangle {       // piquito hacia la mascota
                                width: 10; height: 10; rotation: 45
                                x: -5; y: parent.height / 2 - 5
                                color: T.fillHover
                                border.width: 1; border.color: T.stroke
                                z: -1
                            }
                            // texto completo, invisible: da el tamaño final del globo desde el principio
                            Text {
                                textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                                id: line
                                x: 11; y: 7
                                width: speech.parent.width - 22     // ancho maximo; el globo se ajusta al texto real
                                text: panel.fullLine
                                font.pixelSize: 13
                                wrapMode: Text.Wrap
                                maximumLineCount: 4
                                elide: Text.ElideRight
                                opacity: 0
                            }
                            // lo que se ve: aparece letra por letra, como si hablara
                            Text {
                                textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                                x: 11; y: 7
                                width: line.width
                                text: panel.fullLine.substring(0, panel.typed)
                                color: panel.summary.mood === "waiting" ? "#FF9F0A" : T.text
                                font.pixelSize: 13
                                wrapMode: Text.Wrap
                                maximumLineCount: 4
                                elide: Text.ElideRight
                            }
                            SequentialAnimation {
                                id: pop
                                NumberAnimation { target: speech; property: "scale"; to: 1.04; duration: 90 }
                                NumberAnimation { target: speech; property: "scale"; to: 1.0; duration: 160; easing.type: Easing.OutBack }
                            }
                        }
                        Text {
                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                            width: parent.width
                            leftPadding: 2
                            elide: Text.ElideRight
                            color: T.text3; font.pixelSize: 11
                            text: {
                                var s = panel.summary, p = [];
                                p.push(s.total === 0 ? "Sin sesiones abiertas" : s.total + (s.total === 1 ? " sesión" : " sesiones"));
                                if (s.working) p.push(s.working + " trabajando");
                                if (s.waiting) p.push(s.waiting + (s.waiting === 1 ? " te espera" : " te esperan"));
                                return p.join("  ·  ");
                            }
                        }
                    }
                }

                // --- volver (en la ficha, los ajustes, el historial y el grafico)
                Item {
                    visible: panel.view !== "main"
                    width: parent.width; height: 30
                    Rectangle {
                        id: backBtn
                        anchors.verticalCenter: parent.verticalCenter
                        width: backRow.implicitWidth + 16; height: 28; radius: 9
                        color: backMa.pressed ? T.fillPress : backMa.containsMouse ? T.fillHover : T.fill
                        border.width: 1; border.color: T.stroke
                        Row {
                            id: backRow
                            anchors.centerIn: parent
                            spacing: 4
                            Text { textFormat: Text.PlainText; text: "‹"; color: T.text; font.pixelSize: 17; anchors.verticalCenter: parent.verticalCenter; topPadding: -2 }
                            Text { textFormat: Text.PlainText; text: "Volver"; color: T.text; font.pixelSize: 13; font.weight: Font.Medium; anchors.verticalCenter: parent.verticalCenter }
                        }
                        MouseArea { id: backMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: panel.view = "main" }
                    }
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        anchors { left: backBtn.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: ({ pet: "Ficha de " + ctrl.pet.name, settings: "Ajustes", history: "Historial",
                                 usage: "Consumo por día" })[panel.view] || ""
                        color: T.text; font.pixelSize: 14; font.weight: Font.DemiBold
                    }
                }

                // --- personalizar la mascota (clic en la mascota)
                Rectangle {
                    visible: panel.view === "settings"
                    width: parent.width
                    height: editCol.implicitHeight + 24
                    radius: 14
                    color: T.fill
                    Column {
                        id: editCol
                        x: 12; y: 12
                        width: parent.width - 24
                        spacing: 10
                        Item {
                            width: parent.width; height: 28
                            Text { textFormat: Text.PlainText; anchors.verticalCenter: parent.verticalCenter; text: "Nombre"; color: T.text2; font.pixelSize: 12 }
                            Rectangle {
                                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                width: 190; height: 28; radius: 8
                                color: T.code; border.width: 1; border.color: nameInput.activeFocus ? "#26A96E" : T.stroke
                                TextInput {
                                    id: nameInput
                                    anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                                    verticalAlignment: TextInput.AlignVCenter
                                    text: ctrl.pet.name
                                    color: T.text; font.pixelSize: 13
                                    maximumLength: 18
                                    selectByMouse: true
                                    onEditingFinished: ctrl.setPet("name", text)
                                }
                            }
                        }
                        // --- diseño de la mascota, con vista previa
                        Item {
                            width: parent.width; height: 74
                            Text { textFormat: Text.PlainText; y: 4; text: "Diseño"; color: T.text2; font.pixelSize: 12 }
                            Row {
                                anchors.right: parent.right
                                spacing: 8
                                Repeater {
                                    model: [["clawd", "Clawd", "#D97757"], ["mochi", "Mochi", "#F2EAD8"]]
                                    Rectangle {
                                        readonly property bool chosen: (ctrl.pet.design || "clawd") === modelData[0]
                                        width: 96; height: 72; radius: 12
                                        color: chosen ? "#2626A96E" : designMa.containsMouse ? T.fillHover : T.fill
                                        border.width: chosen ? 1.5 : 1; border.color: chosen ? "#8826A96E" : T.stroke
                                        Pet {
                                            anchors.horizontalCenter: parent.horizontalCenter; y: 2
                                            s: 50; design: modelData[0]; bodyColor: modelData[2]
                                            mood: designMa.containsMouse ? "happy" : "idle"
                                        }
                                        Text { textFormat: Text.PlainText; anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 5 }
                                               text: modelData[1]; color: parent.chosen ? T.text : T.text2; font.pixelSize: 12; font.weight: parent.chosen ? Font.DemiBold : Font.Normal }
                                        MouseArea { id: designMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: ctrl.setPet("design", modelData[0]) }
                                    }
                                }
                            }
                        }
                        Item {
                            width: parent.width; height: 26
                            Text { textFormat: Text.PlainText; anchors.verticalCenter: parent.verticalCenter; text: "Color"; color: T.text2; font.pixelSize: 12 }
                            Row {
                                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                spacing: 8
                                Repeater {
                                    model: ctrl.pet.design === "mochi"
                                       ? ["#F2EAD8", "#CDEFD9", "#FFD9C2", "#DCD3F5", "#CFE6FF", "#FFF0B3", "#D9D9DE"]
                                       : ["#D97757", "#7C9CF5", "#5BC8A8", "#E58FB8", "#B39DDB", "#F2C94C", "#9AA0A6"]
                                    Rectangle {
                                        width: 22; height: 22; radius: 11
                                        color: modelData
                                        border.width: ctrl.pet.color === modelData ? 2 : 0
                                        border.color: T.text
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: ctrl.setPet("color", modelData) }
                                    }
                                }
                            }
                        }
                        Item {
                            width: parent.width; height: 30
                            Text { textFormat: Text.PlainText; anchors.verticalCenter: parent.verticalCenter; text: "Accesorio"; color: T.text2; font.pixelSize: 12 }
                            Row {
                                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                spacing: 3
                                Repeater {
                                    model: ["", "hat", "bow", "glasses", "headphones", "flower", "crown"]
                                    Rectangle {
                                        id: accBtn
                                        readonly property bool locked: ctrl.petState.unlocked.indexOf(modelData) < 0
                                        width: 32; height: 32; radius: 8
                                        color: ctrl.pet.accessory === modelData ? T.fillPress : accMa.containsMouse ? T.fillHover : "transparent"
                                        border.width: ctrl.pet.accessory === modelData ? 1 : 0
                                        border.color: T.stroke
                                        Text {
                                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                                            visible: modelData === ""
                                            anchors.centerIn: parent; text: "∅"; color: T.text2; font.pixelSize: 15
                                        }
                                        Item {         // vista previa: la zona de la cabeza del accesorio
                                            visible: modelData !== ""
                                            anchors.centerIn: parent
                                            width: 26; height: 26
                                            clip: true
                                            opacity: accBtn.locked ? 0.3 : 1
                                            Accessory {
                                                // caja de cada accesorio en el espacio 100x100: [x, y, ancho, alto]
                                                readonly property var box: ({ hat: [29, 3, 42, 26], crown: [31, 8, 38, 21],
                                                    bow: [57, 17, 28, 20], glasses: [13, 43, 74, 12],
                                                    headphones: [5, 10, 90, 47], flower: [16, 16, 20, 20] })[modelData] || [0, 0, 100, 100]
                                                readonly property real k: Math.min(24 / box[2], 24 / box[3])
                                                kind: modelData
                                                scale: k
                                                transformOrigin: Item.TopLeft
                                                x: 13 - (box[0] + box[2] / 2) * k
                                                y: 13 - (box[1] + box[3] / 2) * k
                                            }
                                        }
                                        Rectangle {    // candado: nivel necesario
                                            visible: accBtn.locked
                                            anchors { right: parent.right; bottom: parent.bottom; margins: 1 }
                                            width: lockTxt.implicitWidth + 6; height: 13; radius: 6
                                            color: "#CC1C1C1E"
                                            Text { textFormat: Text.PlainText; id: lockTxt; anchors.centerIn: parent; text: "Nv " + ctrl.petState.unlocks[modelData]; color: "white"; font.pixelSize: 8; font.bold: true }
                                        }
                                        MouseArea {
                                            id: accMa
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: accBtn.locked ? Qt.ForbiddenCursor : Qt.PointingHandCursor
                                            onClicked: if (!accBtn.locked) ctrl.setPet("accessory", modelData)
                                        }
                                    }
                                }
                            }
                        }
                    // --- donde aparecen las notificaciones
                    Item {
                        width: parent.width
                        height: 30
                        Text {
                            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                            anchors.verticalCenter: parent.verticalCenter
                            leftPadding: 2
                            text: "Notificaciones"
                            color: T.text2; font.pixelSize: 12
                        }
                        Rectangle {
                            id: seg
                            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                            width: segRow.implicitWidth + 4; height: 28; radius: 9
                            color: T.fill
                            border.width: 1; border.color: T.stroke
                            Rectangle {        // indicador deslizante
                                y: 2; height: parent.height - 4; radius: 7
                                x: ctrl.toastPosition === "bubble" ? optBubble.x + 2 : optCorner.x + 2
                                width: ctrl.toastPosition === "bubble" ? optBubble.width : optCorner.width
                                color: T.fillPress
                                Behavior on x { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                                Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                            }
                            Row {
                                id: segRow
                                x: 2
                                anchors.verticalCenter: parent.verticalCenter
                                SegOption { id: optCorner; text: "Esquina"; key: "corner" }
                                SegOption { id: optBubble; text: "Burbuja"; key: "bubble" }
                            }
                        }
                    }
                        // --- sonidos: uno por tipo de aviso, elegible con flechas, y boton para escucharlo
                        Column {
                            width: parent.width
                            spacing: 4
                            visible: ctrl.canPlaySound
                            Text { textFormat: Text.PlainText; text: "Sonidos"; color: T.text2; font.pixelSize: 12 }
                            Repeater {
                                model: [["permission", "Cuando pide permiso"], ["question", "Cuando pregunta algo"],
                                        ["done", "Cuando termina"], ["fail", "Cuando hay un error"]]
                                Item {
                                    id: soundRow
                                    readonly property string kind: modelData[0]
                                    readonly property string current: ctrl.sounds[kind] || ""
                                    // posicion en la lista; -1 = sin sonido
                                    readonly property int idx: {
                                        for (var i = 0; i < ctrl.soundLibrary.length; i++)
                                            if (ctrl.soundLibrary[i].key === current) return i
                                        return -1
                                    }
                                    function pick(step) {
                                        var n = ctrl.soundLibrary.length + 1          // + "sin sonido"
                                        var next = ((idx + 1 + step) % n + n) % n - 1
                                        ctrl.setSound(kind, next < 0 ? "" : ctrl.soundLibrary[next].key)
                                    }
                                    width: parent.width; height: 30
                                    Text {
                                        textFormat: Text.PlainText
                                        anchors.verticalCenter: parent.verticalCenter
                                        leftPadding: 8
                                        text: modelData[1]; color: T.text; font.pixelSize: 12
                                    }
                                    Row {
                                        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                        spacing: 4
                                        Rectangle {           // selector: ‹ nombre ›
                                            width: 132; height: 26; radius: 8
                                            color: T.code; border.width: 1; border.color: T.stroke
                                            Text {
                                                textFormat: Text.PlainText
                                                anchors.centerIn: parent
                                                text: soundRow.idx < 0 ? "Sin sonido" : ctrl.soundLibrary[soundRow.idx].label
                                                color: soundRow.idx < 0 ? T.text3 : T.text; font.pixelSize: 12
                                            }
                                            Repeater {
                                                model: [-1, 1]
                                                Rectangle {
                                                    x: modelData < 0 ? 2 : parent.width - width - 2
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    width: 22; height: 22; radius: 6
                                                    color: arrowMa.pressed ? T.fillPress : arrowMa.containsMouse ? T.fillHover : "transparent"
                                                    Text { textFormat: Text.PlainText; anchors.centerIn: parent; text: modelData < 0 ? "‹" : "›"; color: T.text2; font.pixelSize: 16 }
                                                    MouseArea { id: arrowMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: soundRow.pick(modelData) }
                                                }
                                            }
                                        }
                                        Rectangle {           // escuchar
                                            width: 26; height: 26; radius: 8
                                            opacity: soundRow.idx < 0 ? 0.35 : 1
                                            color: playMa.pressed ? T.fillPress : playMa.containsMouse ? T.fillHover : T.fill
                                            border.width: 1; border.color: T.stroke
                                            Text { textFormat: Text.PlainText; anchors.centerIn: parent; anchors.horizontalCenterOffset: 1; text: "▶"; color: T.text2; font.pixelSize: 10 }
                                            MouseArea { id: playMa; anchors.fill: parent; enabled: soundRow.idx >= 0; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: ctrl.previewSound(soundRow.current) }
                                        }
                                    }
                                }
                            }
                        }
                        Item {
                            width: parent.width; height: 26
                            visible: ctrl.canPlaySound
                            Text { textFormat: Text.PlainText; anchors.verticalCenter: parent.verticalCenter; leftPadding: 8; text: "Volumen"; color: T.text; font.pixelSize: 12 }
                            Rectangle {               // deslizador de volumen
                                id: volTrack
                                anchors { right: volLabel.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                                width: 170; height: 6; radius: 3
                                color: T.fill
                                property real value: ctrl.soundVolume / 100
                                Rectangle { width: parent.width * parent.value; height: parent.height; radius: 3; color: "#26A96E" }
                                Rectangle {
                                    x: volTrack.width * volTrack.value - width / 2; anchors.verticalCenter: parent.verticalCenter
                                    width: 16; height: 16; radius: 8
                                    color: "white"; border.width: 1; border.color: T.stroke
                                }
                                MouseArea {
                                    anchors.fill: parent; anchors.margins: -8
                                    cursorShape: Qt.PointingHandCursor
                                    function setFrom(mx) { volTrack.value = Math.max(0, Math.min(1, (mx - 8) / volTrack.width)) }
                                    onPressed: (e) => setFrom(e.x)
                                    onPositionChanged: (e) => { if (pressed) setFrom(e.x) }
                                    onReleased: { ctrl.setSoundVolume(Math.round(volTrack.value * 100)); ctrl.previewSound(ctrl.sounds.permission || "campana") }
                                }
                            }
                            Text { textFormat: Text.PlainText; id: volLabel; anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                   text: Math.round(volTrack.value * 100) + " %"; width: 38; horizontalAlignment: Text.AlignRight
                                   color: T.text2; font.pixelSize: 12 }
                        }
                        // --- atajos de teclado
                        Column {
                            width: parent.width
                            spacing: 4
                            Text { textFormat: Text.PlainText; text: "Atajos de teclado"; color: T.text2; font.pixelSize: 12 }
                            Repeater {
                                model: ctrl.shortcuts.items
                                Item {
                                    width: parent.width; height: 22
                                    Text {
                                        textFormat: Text.PlainText
                                        anchors.verticalCenter: parent.verticalCenter
                                        leftPadding: 8
                                        text: ({ allow: "Permitir la última", deny: "Rechazar la última", panel: "Abrir el panel" })[modelData.action] || modelData.action
                                        color: T.text; font.pixelSize: 12
                                    }
                                    Row {
                                        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                        spacing: 6
                                        Text {
                                            textFormat: Text.PlainText
                                            visible: !modelData.active && ctrl.shortcuts.x11
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.reason; color: "#FF9F0A"; font.pixelSize: 10
                                        }
                                        Rectangle {
                                            width: keyTxt.implicitWidth + 12; height: 20; radius: 5
                                            color: T.code; border.width: 1; border.color: T.stroke
                                            opacity: modelData.active || !ctrl.shortcuts.x11 ? 1 : 0.5
                                            Text { textFormat: Text.PlainText; id: keyTxt; anchors.centerIn: parent; text: modelData.keys; color: T.text2; font.pixelSize: 11; font.family: MONO }
                                        }
                                    }
                                }
                            }
                            Text {
                                textFormat: Text.PlainText
                                width: parent.width
                                leftPadding: 8
                                wrapMode: Text.Wrap
                                color: T.text3; font.pixelSize: 11
                                text: ctrl.shortcuts.x11
                                      ? "Por seguridad, «Permitir» nunca aprueba comandos destructivos."
                                      : "En Wayland, asígnalos en los atajos de tu escritorio con los comandos: traychi --allow, --deny y --panel."
                            }
                        }
                        Item {
                            width: parent.width; height: 28
                            Text { textFormat: Text.PlainText; anchors.verticalCenter: parent.verticalCenter; text: "Icono de la bandeja"; color: T.text2; font.pixelSize: 12 }
                            Row {
                                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                                spacing: 6
                                Btn { kind: ctrl.pet.tray === "pet" ? "glass" : "quiet"; text: "Mascota"; onClicked: ctrl.setPet("tray", "pet") }
                                Btn { kind: ctrl.pet.tray === "glyph" ? "glass" : "quiet"; text: "Simple"; onClicked: ctrl.setPet("tray", "glyph") }
                            }
                        }
                    }
                }

                // --- consumo
                Rectangle {
                    width: parent.width
                    visible: panel.view === "main"
                    height: usageCol.implicitHeight + 26
                    radius: 14
                    color: T.fill
                    Column {
                        id: usageCol
                        x: 14; y: 13
                        width: parent.width - 28
                        spacing: 14
                        UsageBar { width: parent.width; label: "Sesión (5 h)"; pct: panel.usage.five_hour.pct; resets: panel.usage.five_hour.resets; now: panel.now }
                        UsageBar { width: parent.width; label: "Semana (7 d)"; pct: panel.usage.seven_day.pct; resets: panel.usage.seven_day.resets; now: panel.now }
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: { panel.view = "usage"; ctrl.refreshDaily() }
                    }
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        anchors { right: parent.right; rightMargin: 12; bottom: parent.bottom; bottomMargin: 8 }
                        text: "Ver por día ›"
                        color: T.text3; font.pixelSize: 10
                    }
                }

                // --- solicitudes pendientes
                Column {
                    width: parent.width
                    spacing: 8
                    visible: pendingModel.count > 0 && panel.view === "main"
                    SectionLabel { text: "Solicitudes" ; count: pendingModel.count; accent: true }
                    Repeater {
                        model: pendingModel
                        Rectangle {
                            width: col.width
                            height: (model.kind === "question" ? qcard.implicitHeight : ac.implicitHeight) + 24
                            radius: 14
                            color: T.fill
                            border.width: 1; border.color: "#66FF9F0A"
                            ApprovalCard { id: ac; visible: model.kind !== "question"; x: 12; y: 12; width: parent.width - 24; item: model; compact: true; now: panel.now }
                            QuestionCard { id: qcard; visible: model.kind === "question"; x: 12; y: 12; width: parent.width - 24; item: model; compact: true; now: panel.now }
                        }
                    }
                }

                // --- sesiones
                Column {
                    width: parent.width
                    visible: panel.view === "main"
                    spacing: 8
                    SectionLabel { text: "Sesiones"; count: sessionModel.count }
                    Repeater {
                        model: sessionModel
                        SessionRow { width: col.width; s: model; now: panel.now }
                    }
                    Text {
                        visible: sessionModel.count === 0
                        width: parent.width
                        topPadding: 6; bottomPadding: 6
                        horizontalAlignment: Text.AlignHCenter
                        text: "Abre <b>claude</b> en una terminal y aparecerá aquí."
                        textFormat: Text.StyledText
                        color: T.text3; font.pixelSize: 12
                    }
                }

                // --- historial de decisiones (boton del reloj)
                UsageChart {
                    width: parent.width
                    visible: panel.view === "usage"
                }

                PetCard {
                    width: parent.width
                    visible: panel.view === "pet"
                }

                HistoryView {
                    width: parent.width
                    visible: panel.view === "history"
                    now: panel.now
                }

                // --- pie
                Item {
                    width: parent.width
                    height: 28
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        anchors.verticalCenter: parent.verticalCenter
                        color: T.text3; font.pixelSize: 11
                        text: {
                            var p = [];
                            if (panel.usage.updated) p.push("Consumo " + U.ago(panel.usage.updated * 1000, panel.now));
                            if (panel.summary.cost > 0) p.push("$" + panel.summary.cost.toFixed(2) + " equiv. API");
                            return p.join("  ·  ");
                        }
                    }
                    Btn { anchors.right: parent.right; kind: "quiet"; text: "Salir"; onClicked: ctrl.quit() }
                }
            }
        }
    }

    component SegOption: Item {
        property alias text: segText.text
        property string key
        implicitWidth: segText.implicitWidth + 22
        implicitHeight: 24
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            id: segText
            anchors.centerIn: parent
            color: ctrl.toastPosition === parent.key ? T.text : T.text2
            font.pixelSize: 12
            font.weight: ctrl.toastPosition === parent.key ? Font.DemiBold : Font.Normal
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: ctrl.setToastPosition(parent.key) }
    }

    component SectionLabel: Row {
        property alias text: lbl.text
        property int count: 0
        property bool accent: false
        spacing: 6
        leftPadding: 2
        Text { textFormat: Text.PlainText; id: lbl; color: T.text2; font.pixelSize: 12; font.weight: Font.DemiBold; font.capitalization: Font.AllUppercase; font.letterSpacing: 0.5 }
        Rectangle {
            visible: count > 0
            anchors.verticalCenter: parent.verticalCenter
            width: Math.max(16, cnt.implicitWidth + 8); height: 16; radius: 8
            color: accent ? "#FF9F0A" : T.fillHover
            Text { textFormat: Text.PlainText; id: cnt; anchors.centerIn: parent; text: count; color: accent ? "black" : T.text2; font.pixelSize: 10; font.weight: Font.Bold }
        }
    }
}
