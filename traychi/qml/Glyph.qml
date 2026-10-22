import QtQuick
import QtQuick.Shapes

// La mascota en miniatura (solo la cara), en su diseño: marca de Traychi en las notificaciones.
Item {
    id: g
    readonly property string design: ctrl && ctrl.pet ? ctrl.pet.design : "clawd"
    property color color: ctrl && ctrl.pet ? ctrl.pet.color : "#D97757"
    property bool spinning: false          // compatibilidad: ya no gira
    implicitWidth: 20
    implicitHeight: 20

    // diseño "clawd": cara del robotito
    Rectangle {
        visible: g.design !== "mochi"
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

    // diseño "mochi": cara de mochi con el brote
    Item {
        visible: g.design === "mochi"
        width: 100; height: 100
        scale: Math.min(g.width, g.height) / 100
        transformOrigin: Item.TopLeft
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                fillColor: g.color; strokeColor: Qt.darker(g.color, 1.2); strokeWidth: 4
                PathSvg { path: "M 50 30 C 78 30 94 46 94 64 C 94 84 76 94 50 94 C 24 94 6 84 6 64 C 6 46 22 30 50 30 Z" }
            }
            ShapePath {
                fillColor: "#48BE94"; strokeColor: "transparent"
                PathSvg { path: "M 50 30 C 42 12 26 10 20 16 C 26 28 40 32 50 30 Z" }
            }
            ShapePath {
                fillColor: "#57D09D"; strokeColor: "transparent"
                PathSvg { path: "M 52 29 C 60 14 74 12 80 17 C 74 27 62 31 52 29 Z" }
            }
        }
        Repeater {
            model: [34, 66]
            Rectangle { x: modelData - 5; y: 52; width: 10; height: 16; radius: 5; color: "#2A2320" }
        }
    }
}
