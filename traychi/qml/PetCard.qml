import QtQuick

// Ficha de la mascota (clic en ella): nivel, necesidades, estadisticas y acciones.
Column {
    id: pc
    spacing: 12
    readonly property var st: ctrl.petState
    readonly property var hs: ctrl.historyStats

    // --- nivel y experiencia
    Rectangle {
        width: parent.width
        height: lvlCol.implicitHeight + 24
        radius: 14
        color: T.fill
        Column {
            id: lvlCol
            x: 12; y: 12
            width: parent.width - 24
            spacing: 8
            Item {
                width: parent.width; height: 22
                Text {
                    textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Experiencia"
                    color: T.text; font.pixelSize: 14; font.weight: Font.DemiBold
                }
                Rectangle {
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    width: lvl.implicitWidth + 16; height: 22; radius: 11
                    color: "#3326A96E"
                    border.width: 1; border.color: "#6626A96E"
                    Text { textFormat: Text.PlainText; id: lvl; anchors.centerIn: parent; text: "Nivel " + pc.st.level; color: "#7BE8B3"; font.pixelSize: 12; font.weight: Font.Bold }
                }
            }
            Rectangle {
                width: parent.width; height: 6; radius: 3
                color: T.fill
                Rectangle {
                    height: parent.height; radius: 3
                    width: Math.max(height, parent.width * pc.st.progress)
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#7BE8B3" }
                        GradientStop { position: 1; color: "#26A96E" }
                    }
                    Behavior on width { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
                }
            }
            Text {
                textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                text: pc.st.xp + " XP · faltan " + pc.st.toNext + " para el nivel " + (pc.st.level + 1)
                color: T.text3; font.pixelSize: 11
            }
        }
    }

    // --- necesidades
    Rectangle {
        width: parent.width
        height: needs.implicitHeight + 24
        radius: 14
        color: T.fill
        Column {
            id: needs
            x: 12; y: 12
            width: parent.width - 24
            spacing: 10
            NeedBar { label: "Saciedad"; value: pc.st.hunger; tint: "#30D158" }
            NeedBar { label: "Energía"; value: pc.st.energy; tint: "#64D2FF" }
            NeedBar { label: "Cariño"; value: pc.st.happy; tint: "#FF5A7A" }
        }
    }

    // --- estadisticas
    Flow {
        width: parent.width
        spacing: 6
        Chip { text: pc.st.ageDays === 0 ? "Nació hoy" : (pc.st.ageDays + (pc.st.ageDays === 1 ? " día de vida" : " días de vida")) }
        Chip { text: pc.hs.allowed + " aprobadas" }
        Chip { text: pc.hs.done + " tareas terminadas" }
        Chip { visible: pc.hs.streak > 0; text: "racha de " + pc.hs.streak + (pc.hs.streak === 1 ? " día" : " días") }
    }

    // --- accesorios: se desbloquean subiendo de nivel; un clic se lo pone, otro se lo saca
    Text {
        textFormat: Text.PlainText
        text: "ACCESORIOS"
        color: T.text2; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 0.5
        leftPadding: 2
    }
    Flow {
        width: parent.width
        spacing: 8
        Repeater {
            model: ["hat", "bow", "glasses", "headphones", "flower", "crown"]
            Rectangle {
                id: accBtn
                readonly property bool locked: pc.st.unlocked.indexOf(modelData) < 0
                readonly property bool isNew: (pc.st.newUnlocks || []).indexOf(modelData) >= 0
                readonly property bool worn: ctrl.pet.accessory === modelData
                width: (pc.width - 5 * 8) / 6; height: width
                radius: 12
                color: worn ? "#2626A96E" : accMa.containsMouse && !locked ? T.fillHover : T.fill
                border.width: worn || isNew ? 1.5 : 1
                border.color: worn ? "#8826A96E" : isNew ? "#FFD60A" : T.stroke
                Item {             // vista previa centrada segun el tamaño de cada accesorio
                    anchors.centerIn: parent
                    width: parent.width - 12; height: width
                    clip: true
                    opacity: accBtn.locked ? 0.28 : 1
                    Accessory {
                        readonly property var box: ({ hat: [29, 3, 42, 26], crown: [31, 8, 38, 21],
                            bow: [57, 17, 28, 20], glasses: [13, 43, 74, 12],
                            headphones: [5, 10, 90, 47], flower: [16, 16, 20, 20] })[modelData]
                        readonly property real k: Math.min(parent.width / box[2], parent.height / box[3]) * 0.9
                        kind: modelData
                        scale: k
                        transformOrigin: Item.TopLeft
                        x: parent.width / 2 - (box[0] + box[2] / 2) * k
                        y: parent.height / 2 - (box[1] + box[3] / 2) * k
                    }
                }
                Rectangle {        // candado: nivel necesario
                    visible: accBtn.locked
                    anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 4 }
                    width: lockTxt.implicitWidth + 10; height: 15; radius: 7
                    color: "#CC1C1C1E"
                    Text { textFormat: Text.PlainText; id: lockTxt; anchors.centerIn: parent; text: "Nv " + pc.st.unlocks[modelData]; color: "white"; font.pixelSize: 9; font.bold: true }
                }
                Rectangle {        // recien desbloqueado
                    visible: accBtn.isNew
                    anchors { right: parent.right; top: parent.top; margins: -5 }
                    width: newTxt.implicitWidth + 10; height: 16; radius: 8
                    color: "#FFD60A"
                    Text { textFormat: Text.PlainText; id: newTxt; anchors.centerIn: parent; text: "Nuevo"; color: "black"; font.pixelSize: 9; font.bold: true }
                    SequentialAnimation on scale {
                        running: accBtn.isNew; loops: Animation.Infinite
                        NumberAnimation { to: 1.12; duration: 500; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 500; easing.type: Easing.InOutSine }
                    }
                }
                MouseArea {
                    id: accMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: accBtn.locked ? Qt.ForbiddenCursor : Qt.PointingHandCursor
                    onClicked: if (!accBtn.locked) ctrl.setPet("accessory", accBtn.worn ? "" : modelData)
                }
            }
        }
    }
    Text {
        textFormat: Text.PlainText
        width: parent.width
        leftPadding: 2
        wrapMode: Text.Wrap
        color: T.text3; font.pixelSize: 11
        text: {
            var next = null, names = { hat: "el sombrero", bow: "el moño", glasses: "los lentes",
                                       headphones: "los audífonos", flower: "la flor", crown: "la corona" }
            for (var k in pc.st.unlocks)
                if (k && pc.st.unlocked.indexOf(k) < 0 && (!next || pc.st.unlocks[k] < pc.st.unlocks[next])) next = k
            return next ? "Próximo: " + names[next] + " en el nivel " + pc.st.unlocks[next] + " · un clic para ponerlo o sacarlo"
                        : "¡Tienes todos los accesorios! · un clic para ponerlo o sacarlo"
        }
    }

    // --- acciones
    Text {
        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
        text: "DAR DE COMER"
        color: T.text2; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 0.5
        leftPadding: 2
    }
    Row {
        spacing: 8
        Repeater {
            model: ctrl.foods
            Rectangle {
                width: (pc.width - 16) / 3; height: 40; radius: 12
                color: foodMa.pressed ? T.fillPress : foodMa.containsMouse ? T.fillHover : T.fill
                border.width: 1; border.color: T.stroke
                scale: foodMa.pressed ? 0.96 : 1
                Behavior on scale { NumberAnimation { duration: 120 } }
                Row {
                    anchors.centerIn: parent
                    spacing: 7
                    FoodIcon { kind: modelData.key; size: 20; anchors.verticalCenter: parent.verticalCenter }
                    Text {
                        textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.name.charAt(0).toUpperCase() + modelData.name.slice(1)
                        color: T.text; font.pixelSize: 13; font.weight: Font.Medium
                    }
                }
                MouseArea {
                    id: foodMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: ctrl.feedPet(modelData.key)
                }
            }
        }
    }
    Row {
        spacing: 8
        Btn { text: "Jugar"; width: (pc.width - 8) / 2; onClicked: ctrl.playPet() }
        Btn { text: "Acariciar"; width: (pc.width - 8) / 2; onClicked: ctrl.caressPet() }
    }

    component NeedBar: Column {
        property string label
        property real value: 0
        property color tint: "#30D158"
        width: parent ? parent.width : 300
        spacing: 5
        Item {
            width: parent.width; height: 16
            Text { textFormat: Text.PlainText; text: label; color: T.text; font.pixelSize: 12; font.weight: Font.Medium }
            Text {
                textFormat: Text.PlainText   // nunca interpretar HTML del contenido
                anchors.right: parent.right
                text: Math.round(value) + " %"
                color: value < 25 ? "#FF9F0A" : T.text2
                font.pixelSize: 12
                font.features: { "tnum": 1 }
            }
        }
        Rectangle {
            width: parent.width; height: 6; radius: 3
            color: T.fill
            Rectangle {
                height: parent.height; radius: 3
                width: Math.max(value > 0 ? height : 0, parent.width * value / 100)
                color: value < 25 ? "#FF9F0A" : tint
                Behavior on width { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
                Behavior on color { ColorAnimation { duration: 300 } }
            }
        }
    }
}
