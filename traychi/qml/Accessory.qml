import QtQuick
import QtQuick.Shapes

// Accesorios de la mascota dibujados en vectores, en un espacio de 100x100
// alineado con Pet.qml (cuerpo: x 12..88, y 26..86; ojos en 38 y 62, y ~47).
Item {
    id: acc
    property string kind: ""
    width: 100; height: 100

    // --- sombrero de copa
    Item {
        visible: acc.kind === "hat"
        anchors.fill: parent
        Rectangle { x: 37; y: 3; width: 26; height: 23; radius: 3; color: "#2C2C30" }
        Rectangle { x: 37; y: 17; width: 26; height: 4; color: "#D0453A" }
        Rectangle { x: 29; y: 24; width: 42; height: 5; radius: 2.5; color: "#232327" }
        Rectangle { x: 40; y: 5; width: 4; height: 11; radius: 2; color: "#30FFFFFF" }
    }

    // --- corona
    Shape {
        visible: acc.kind === "crown"
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: "#F5C542"; strokeColor: "#C99A1E"; strokeWidth: 1.2
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: "M32 29 L31 13 L41 21 L50 8 L59 21 L69 13 L68 29 Z" }
        }
        ShapePath {
            fillColor: "#E5484D"; strokeColor: "transparent"
            PathSvg { path: "M50 19 m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0" }
        }
        ShapePath {
            fillColor: "#4CC3FF"; strokeColor: "transparent"
            PathSvg { path: "M38 24 m-2 0 a2 2 0 1 0 4 0 a2 2 0 1 0 -4 0 M62 24 m-2 0 a2 2 0 1 0 4 0 a2 2 0 1 0 -4 0" }
        }
    }

    // --- moño
    Shape {
        visible: acc.kind === "bow"
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: "#FF7EB6"; strokeColor: "#E0609A"; strokeWidth: 1.2
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: "M71 27 Q63 17 59 21 Q57 27 59 33 Q63 37 71 27 Z M71 27 Q79 17 83 21 Q85 27 83 33 Q79 37 71 27 Z" }
        }
        ShapePath {
            fillColor: "#E0609A"; strokeColor: "transparent"
            PathSvg { path: "M71 27 m-3.5 0 a3.5 3.5 0 1 0 7 0 a3.5 3.5 0 1 0 -7 0" }
        }
    }

    // --- lentes de sol
    Item {
        visible: acc.kind === "glasses"
        anchors.fill: parent
        Rectangle { x: 18; y: 46; width: 13; height: 2.4; color: "#1C1C1E" }
        Rectangle { x: 71; y: 46; width: 12; height: 2.4; color: "#1C1C1E" }
        Rectangle { x: 46; y: 47; width: 10; height: 2.4; color: "#1C1C1E" }
        Rectangle { x: 30; y: 43; width: 18; height: 12; radius: 4; color: "#1C1C1E" }
        Rectangle { x: 54; y: 43; width: 18; height: 12; radius: 4; color: "#1C1C1E" }
        Rectangle { x: 33; y: 45; width: 6; height: 2.5; radius: 1.2; color: "#55FFFFFF" }
        Rectangle { x: 57; y: 45; width: 6; height: 2.5; radius: 1.2; color: "#55FFFFFF" }
    }

    // --- audífonos
    Item {
        visible: acc.kind === "headphones"
        anchors.fill: parent
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                fillColor: "transparent"; strokeColor: "#3A3A3C"; strokeWidth: 5
                capStyle: ShapePath.RoundCap
                PathSvg { path: "M12 44 C12 8, 88 8, 88 44" }
            }
        }
        Rectangle { x: 5; y: 37; width: 11; height: 20; radius: 5; color: "#3A3A3C" }
        Rectangle { x: 84; y: 37; width: 11; height: 20; radius: 5; color: "#3A3A3C" }
        Rectangle { x: 8; y: 41; width: 5; height: 12; radius: 2.5; color: "#5E5CE6" }
        Rectangle { x: 87; y: 41; width: 5; height: 12; radius: 2.5; color: "#5E5CE6" }
    }

    // --- flor
    Item {
        visible: acc.kind === "flower"
        anchors.fill: parent
        Repeater {
            model: 5
            Rectangle {
                readonly property real a: index * 2 * Math.PI / 5 - Math.PI / 2
                width: 10; height: 10; radius: 5
                x: 26 + 5.5 * Math.cos(a) - 5; y: 26 + 5.5 * Math.sin(a) - 5
                color: "#FFB3D1"
                border.width: 0.8; border.color: "#F58DB8"
            }
        }
        Rectangle { x: 22.5; y: 22.5; width: 7; height: 7; radius: 3.5; color: "#FFD60A" }
    }
}
