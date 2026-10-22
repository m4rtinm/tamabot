import QtQuick
import QtQuick.Effects
import QtQuick.Shapes

// Superficie de vidrio: tinte translucido sobre el desenfoque de KWin,
// brillo superior y un borde de luz muy fino. Con tail != 0 se dibuja
// como burbuja con un pico (1 = hacia abajo, -1 = hacia arriba) en tailX.
Item {
    id: root
    property real radius: 20
    property bool strong: false
    property bool shadow: true
    property int tail: 0
    property real tailX: width / 2
    property real tailSize: 10
    default property alias content: inner.data

    readonly property color tint: root.strong ? T.tintStrong : T.tint

    RectangularShadow {
        visible: root.shadow
        anchors.fill: parent
        radius: root.radius
        blur: 30
        offset.y: 10
        color: T.shadow
    }

    Rectangle {
        visible: root.tail === 0
        anchors.fill: parent
        radius: root.radius
        color: root.tint
        border.width: 1
        border.color: T.stroke
    }

    Shape {
        visible: root.tail !== 0
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: root.tint
            strokeColor: T.stroke
            strokeWidth: 1
            PathSvg { path: root.bubblePath() }
        }
    }

    Rectangle {          // brillo superior
        anchors.fill: parent
        anchors.margins: 1
        radius: root.radius - 1
        gradient: Gradient {
            GradientStop { position: 0.0; color: T.sheen }
            GradientStop { position: 0.5; color: "transparent" }
        }
    }
    Rectangle {          // borde de luz
        height: 1
        anchors { top: parent.top; left: parent.left; right: parent.right; leftMargin: root.radius; rightMargin: root.radius }
        visible: root.tail !== -1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.5; color: T.rim }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    Item { id: inner; anchors.fill: parent }

    function bubblePath() {
        var w = width - 1, h = height - 1, r = radius, s = tailSize, o = 0.5;
        var x = Math.max(r + s + 2, Math.min(w - r - s - 2, tailX));
        var p = "M " + (r + o) + " " + o + " ";
        if (tail === -1)
            p += "L " + (x - s) + " " + o + " L " + (x - 2) + " " + (-s + 1.5) + " Q " + x + " " + (-s) + " " + (x + 2) + " " + (-s + 1.5)
               + " L " + (x + s) + " " + o + " ";
        p += "L " + (w - r) + " " + o + " A " + r + " " + r + " 0 0 1 " + w + " " + (r + o)
           + " L " + w + " " + (h - r) + " A " + r + " " + r + " 0 0 1 " + (w - r) + " " + h + " ";
        if (tail === 1)
            p += "L " + (x + s) + " " + h + " L " + (x + 2) + " " + (h + s - 1.5) + " Q " + x + " " + (h + s) + " " + (x - 2) + " " + (h + s - 1.5)
               + " L " + (x - s) + " " + h + " ";
        p += "L " + (r + o) + " " + h + " A " + r + " " + r + " 0 0 1 " + o + " " + (h - r)
           + " L " + o + " " + (r + o) + " A " + r + " " + r + " 0 0 1 " + (r + o) + " " + o + " Z";
        return p;
    }
}
