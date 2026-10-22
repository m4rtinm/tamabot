import QtQuick
import QtQuick.Shapes

// Boton redondo con icono de linea (trazos estilo Lucide, 24x24).
Rectangle {
    id: b
    property string icon: "bell"
    property bool active: false
    signal clicked()

    readonly property var paths: ({
        "bell": "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9 M10.3 21a1.94 1.94 0 0 0 3.4 0",
        "bell-off": "M8.7 3A6 6 0 0 1 18 8a21.3 21.3 0 0 0 .6 5 M17 17H3s3-2 3-9a4.67 4.67 0 0 1 .3-1.7 M10.3 21a1.94 1.94 0 0 0 3.4 0 M2 2L22 22",
        "history": "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8 M3 3v5h5 M12 7v5l4 2",
        "settings": "M20 7h-9 M14 17H5 M10 7a3 3 0 1 1-6 0a3 3 0 1 1 6 0 M20 17a3 3 0 1 1-6 0a3 3 0 1 1 6 0"
    })

    implicitWidth: 28
    implicitHeight: 28
    radius: 9
    color: ma.pressed ? T.fillPress : (ma.containsMouse || active) ? T.fillHover : "transparent"
    border.width: active ? 1 : 0
    border.color: T.stroke
    scale: ma.pressed ? 0.94 : 1
    Behavior on color { ColorAnimation { duration: 120 } }
    Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }

    Item {
        width: 24; height: 24
        anchors.centerIn: parent
        scale: 16 / 24
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: b.active || ma.containsMouse ? T.text : T.text2
                strokeWidth: 2.2
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                joinStyle: ShapePath.RoundJoin
                PathSvg { path: b.paths[b.icon] || "" }
            }
        }
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: b.clicked()
    }
}
