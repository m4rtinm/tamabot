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
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Experiencia"
                    color: T.text; font.pixelSize: 14; font.weight: Font.DemiBold
                }
                Rectangle {
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    width: lvl.implicitWidth + 16; height: 22; radius: 11
                    color: "#33D97757"
                    border.width: 1; border.color: "#66D97757"
                    Text { id: lvl; anchors.centerIn: parent; text: "Nivel " + pc.st.level; color: "#F0A585"; font.pixelSize: 12; font.weight: Font.Bold }
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
                        GradientStop { position: 0; color: "#F0A585" }
                        GradientStop { position: 1; color: "#D97757" }
                    }
                    Behavior on width { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
                }
            }
            Text {
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

    // --- acciones
    Text {
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
            Text { text: label; color: T.text; font.pixelSize: 12; font.weight: Font.Medium }
            Text {
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
