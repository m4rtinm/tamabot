import QtQuick

// Carita de Bit (la mascota) en miniatura: marca de Tamabot en las notificaciones.
Item {
    id: g
    property color color: ctrl && ctrl.pet ? ctrl.pet.color : "#D97757"
    property bool spinning: false          // compatibilidad: ya no gira
    implicitWidth: 20
    implicitHeight: 20

    Rectangle {
        anchors.centerIn: parent
        width: g.width * 0.92; height: g.height * 0.68
        radius: height * 0.28
        color: g.color
        Repeater {
            model: [0.3, 0.62]
            Rectangle {
                x: parent.width * modelData; y: parent.height * 0.28
                width: parent.width * 0.1; height: parent.height * 0.34; radius: width / 2
                color: "#2B1D17"
            }
        }
    }
}
