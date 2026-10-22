import QtQuick
import QtQuick.Shapes

// Comida dibujada en vectores (espacio 24x24): apple | pizza | cookie.
Item {
    id: f
    property string kind: "apple"
    property real size: 20
    width: size; height: size

    Item {
        width: 24; height: 24
        scale: f.size / 24
        transformOrigin: Item.TopLeft

        Shape {
            visible: f.kind === "apple"
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                fillColor: "#E5484D"; strokeColor: "transparent"
                PathSvg { path: "M12 7 C8 4 3 6 3 12 C3 18 7 22 10 21 C11 20.6 13 20.6 14 21 C17 22 21 18 21 12 C21 6 16 4 12 7 Z" }
            }
            ShapePath {
                fillColor: "transparent"; strokeColor: "#7A4A2A"; strokeWidth: 1.6
                capStyle: ShapePath.RoundCap
                PathSvg { path: "M12 7 C12 5 12.5 3.5 13.5 2.5" }
            }
            ShapePath {
                fillColor: "#5BC85B"; strokeColor: "transparent"
                PathSvg { path: "M13 5 C14 2 18 2 19 3 C17 6 14 6 13 5 Z" }
            }
            ShapePath {
                fillColor: "#40FFFFFF"; strokeColor: "transparent"
                PathSvg { path: "M6 11 C6 9 7.5 8 9 8 C8 9.5 7.5 11 6 11 Z" }
            }
        }

        Shape {
            visible: f.kind === "pizza"
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                fillColor: "#F7C948"; strokeColor: "#D99A2B"; strokeWidth: 1.2
                joinStyle: ShapePath.RoundJoin
                PathSvg { path: "M3 6 Q12 2 21 6 L12 22 Z" }
            }
            ShapePath {
                fillColor: "#C9792E"; strokeColor: "transparent"
                PathSvg { path: "M3 6 Q12 2 21 6 L20.2 7.6 Q12 4 3.8 7.6 Z" }
            }
            ShapePath {
                fillColor: "#D9433B"; strokeColor: "transparent"
                PathSvg { path: "M9 9 m-1.8 0 a1.8 1.8 0 1 0 3.6 0 a1.8 1.8 0 1 0 -3.6 0 M15 10 m-1.8 0 a1.8 1.8 0 1 0 3.6 0 a1.8 1.8 0 1 0 -3.6 0 M12 15 m-1.6 0 a1.6 1.6 0 1 0 3.2 0 a1.6 1.6 0 1 0 -3.2 0" }
            }
        }

        Shape {
            visible: f.kind === "cookie"
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                fillColor: "#D29A5C"; strokeColor: "#B07B40"; strokeWidth: 1.2
                PathSvg { path: "M12 3 m-9 9 a9 9 0 1 0 18 0 a9 9 0 1 0 -18 0" }
            }
            ShapePath {
                fillColor: "#5A3A22"; strokeColor: "transparent"
                PathSvg { path: "M8 9 m-1.5 0 a1.5 1.5 0 1 0 3 0 a1.5 1.5 0 1 0 -3 0 M15 8 m-1.3 0 a1.3 1.3 0 1 0 2.6 0 a1.3 1.3 0 1 0 -2.6 0 M11 14 m-1.5 0 a1.5 1.5 0 1 0 3 0 a1.5 1.5 0 1 0 -3 0 M16 15 m-1.2 0 a1.2 1.2 0 1 0 2.4 0 a1.2 1.2 0 1 0 -2.4 0 M7 15.5 m-1 0 a1 1 0 1 0 2 0 a1 1 0 1 0 -2 0" }
            }
        }
    }
}
