import QtQuick
import "util.js" as U

Item {
    id: d
    property string status: "idle"
    implicitWidth: 10
    implicitHeight: 10

    Rectangle {          // halo que late mientras trabaja o espera
        id: halo
        anchors.centerIn: parent
        width: parent.width; height: width; radius: width / 2
        color: U.stateColor(d.status)
        opacity: 0
        visible: d.status === "working" || d.status === "waiting"
        SequentialAnimation on scale {
            running: halo.visible; loops: Animation.Infinite
            NumberAnimation { from: 1; to: 2.4; duration: d.status === "waiting" ? 900 : 1400; easing.type: Easing.OutCubic }
        }
        SequentialAnimation on opacity {
            running: halo.visible; loops: Animation.Infinite
            NumberAnimation { from: 0.45; to: 0; duration: d.status === "waiting" ? 900 : 1400; easing.type: Easing.OutCubic }
        }
    }
    Rectangle {
        anchors.centerIn: parent
        width: parent.width; height: width; radius: width / 2
        color: U.stateColor(d.status)
        Behavior on color { ColorAnimation { duration: 250 } }
    }
}
