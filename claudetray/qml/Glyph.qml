import QtQuick

// Destello de Claude dibujado a mano (12 rayos alternos).
Canvas {
    id: c
    property color color: "#D97757"
    property bool spinning: false
    implicitWidth: 20
    implicitHeight: 20
    onColorChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d"), s = Math.min(width, height);
        ctx.reset();
        ctx.strokeStyle = c.color;
        ctx.lineCap = "round";
        ctx.lineWidth = s * 0.105;
        var cx = width / 2, cy = height / 2, r0 = s * 0.07;
        for (var i = 0; i < 12; i++) {
            var a = (i * 30 + (i % 2 ? 6 : 0)) * Math.PI / 180;
            var len = s * (i % 2 === 0 ? 0.46 : 0.36);
            ctx.beginPath();
            ctx.moveTo(cx + r0 * Math.cos(a), cy + r0 * Math.sin(a));
            ctx.lineTo(cx + len * Math.cos(a), cy + len * Math.sin(a));
            ctx.stroke();
        }
    }

    RotationAnimator on rotation {
        running: c.spinning
        from: 0; to: 360
        duration: 6000
        loops: Animation.Infinite
    }
    Behavior on rotation { enabled: !c.spinning; NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
    onSpinningChanged: if (!spinning) rotation = 0
}
