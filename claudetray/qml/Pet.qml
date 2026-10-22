import QtQuick
import QtQuick.Shapes

// Mascota estilo Clawd.
// mood:  idle | working | thinking | waiting | happy | celebrate | hungry | tired
//        | sleep | bored | worried | eat | play | love
// emote: "" | "!" | "?" | sweat | heart | dots | zz | sparkle | confetti | food
Item {
    id: pet
    property real s: 64
    property string mood: "idle"
    property string emote: ""
    property color bodyColor: "#D97757"
    property string accessory: ""
    property bool talking: false       // mueve la boca mientras aparece su frase
    implicitWidth: s
    implicitHeight: s

    readonly property color eyeColor: "#2B1D17"
    readonly property bool joyful: mood === "happy" || mood === "celebrate" || mood === "love" || mood === "play" || mood === "eat"

    // --- propiedades animadas
    property real hop: 0           // salto (negativo = arriba), en px
    property real squash: 1        // 1 normal; <1 aplastado; >1 estirado
    property real look: 0          // mirada horizontal (-1..1)
    property real lookUp: 0        // mirada hacia arriba (0..1)
    property real sway: 0          // balanceo (grados)
    property real chomp: 0         // boca al comer (0..1)
    property real spin: 0          // voltereta al jugar (grados)
    property bool blink: false
    readonly property real eyeOpen: mood === "sleep" ? 0.12
                                   : mood === "tired" ? 0.42
                                   : mood === "bored" ? 0.55
                                   : mood === "hungry" ? 0.8
                                   : (mood === "waiting" || mood === "worried") ? 1.15 : 1

    Behavior on hop { enabled: !anyJump.running; SpringAnimation { spring: 4; damping: 0.3 } }
    Behavior on squash { enabled: !anyJump.running; SpringAnimation { spring: 5; damping: 0.25 } }
    Behavior on look { SpringAnimation { spring: 3; damping: 0.35 } }
    Behavior on lookUp { SpringAnimation { spring: 3; damping: 0.35 } }
    Behavior on sway { SpringAnimation { spring: 2; damping: 0.2 } }

    onMoodChanged: {
        hop = 0; squash = 1; chomp = 0; spin = 0
        look = mood === "bored" ? 0.8 : 0
        lookUp = mood === "thinking" ? 1 : 0
        sway = 0
    }

    // --- saltos con anticipacion y aterrizaje (squash & stretch)
    component Jump: SequentialAnimation {
        property real jumpHeight: 0.12
        property int rest: 600
        NumberAnimation { target: pet; property: "squash"; to: 0.88; duration: 110; easing.type: Easing.OutQuad }
        ParallelAnimation {
            NumberAnimation { target: pet; property: "hop"; to: -pet.s * jumpHeight; duration: 230; easing.type: Easing.OutCubic }
            NumberAnimation { target: pet; property: "squash"; to: 1.08; duration: 160; easing.type: Easing.OutQuad }
        }
        ParallelAnimation {
            NumberAnimation { target: pet; property: "hop"; to: 0; duration: 210; easing.type: Easing.InCubic }
            NumberAnimation { target: pet; property: "squash"; to: 1; duration: 210 }
        }
        NumberAnimation { target: pet; property: "squash"; to: 0.86; duration: 70; easing.type: Easing.OutQuad }
        NumberAnimation { target: pet; property: "squash"; to: 1; duration: 260; easing.type: Easing.OutBack; easing.overshoot: 2.2 }
        PauseAnimation { duration: rest }
    }
    Item {
        id: anyJump
        readonly property bool running: happyJump.running || bigJump.running || playJump.running
        Jump { id: happyJump; running: pet.mood === "happy" || pet.mood === "love"; loops: Animation.Infinite; jumpHeight: 0.12; rest: 700 }
        Jump { id: bigJump; running: pet.mood === "celebrate"; loops: Animation.Infinite; jumpHeight: 0.2; rest: 250 }
        Jump { id: playJump; running: pet.mood === "play"; loops: Animation.Infinite; jumpHeight: 0.22; rest: 80 }
    }

    // trabajando: rebote suave y mirar a los lados
    SequentialAnimation {
        running: pet.mood === "working"; loops: Animation.Infinite
        ParallelAnimation {
            NumberAnimation { target: pet; property: "hop"; to: -pet.s * 0.04; duration: 280; easing.type: Easing.InOutSine }
            NumberAnimation { target: pet; property: "squash"; to: 1.03; duration: 280; easing.type: Easing.InOutSine }
        }
        ParallelAnimation {
            NumberAnimation { target: pet; property: "hop"; to: 0; duration: 280; easing.type: Easing.InOutSine }
            NumberAnimation { target: pet; property: "squash"; to: 0.97; duration: 280; easing.type: Easing.InOutSine }
        }
    }
    SequentialAnimation {
        running: pet.mood === "working"; loops: Animation.Infinite
        ScriptAction { script: pet.look = -1 }
        PauseAnimation { duration: 1300 }
        ScriptAction { script: pet.look = 1 }
        PauseAnimation { duration: 1300 }
    }
    // respirar (dormido, cansado, aburrido, pensando)
    SequentialAnimation {
        running: pet.mood === "sleep" || pet.mood === "tired" || pet.mood === "bored" || pet.mood === "thinking"
        loops: Animation.Infinite
        NumberAnimation { target: pet; property: "squash"; to: 0.96; duration: 1400; easing.type: Easing.InOutSine }
        NumberAnimation { target: pet; property: "squash"; to: 1.0; duration: 1400; easing.type: Easing.InOutSine }
    }
    // balanceo (cansado / con hambre) y temblor (preocupado)
    SequentialAnimation {
        running: pet.mood === "tired" || pet.mood === "hungry"; loops: Animation.Infinite
        NumberAnimation { target: pet; property: "sway"; to: -4; duration: 1200; easing.type: Easing.InOutSine }
        NumberAnimation { target: pet; property: "sway"; to: 4; duration: 1200; easing.type: Easing.InOutSine }
    }
    SequentialAnimation {
        running: pet.mood === "worried"; loops: Animation.Infinite
        NumberAnimation { target: bot; property: "x"; to: pet.s * 0.012; duration: 60 }
        NumberAnimation { target: bot; property: "x"; to: -pet.s * 0.012; duration: 60 }
        NumberAnimation { target: bot; property: "x"; to: 0; duration: 60 }
        PauseAnimation { duration: 900 }
    }
    // jugar: una voltereta en cada salto
    NumberAnimation {
        running: pet.mood === "play"; loops: Animation.Infinite
        target: pet; property: "spin"; from: 0; to: 360; duration: 1100; easing.type: Easing.InOutCubic
    }
    // comer o hablar: abrir y cerrar la boca
    onTalkingChanged: if (!talking && mood !== "eat") chomp = 0
    SequentialAnimation {
        running: pet.mood === "eat" || (pet.talking && !pet.joyful); loops: Animation.Infinite
        NumberAnimation { target: pet; property: "chomp"; to: 1; duration: 140 }
        NumberAnimation { target: pet; property: "chomp"; to: 0.15; duration: 160 }
    }
    // parpadeo
    Timer {
        running: pet.eyeOpen > 0.3 && !pet.joyful
        repeat: true
        interval: 2800 + Math.random() * 2600
        onTriggered: { pet.blink = true; unblink.start() }
    }
    Timer { id: unblink; interval: 130; onTriggered: pet.blink = false }

    // --- sombra (se achica al saltar)
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: pet.s * 0.9
        width: pet.s * 0.62 * Math.max(0.5, 1 + pet.hop / pet.s * 1.6); height: pet.s * 0.07; radius: height / 2
        color: "#40000000"
    }

    Item {
        id: bot
        width: pet.s; height: pet.s
        y: pet.hop
        rotation: pet.sway + pet.spin
        transform: Scale {
            origin.x: pet.s / 2; origin.y: pet.s * 0.86
            xScale: 1 + (1 - pet.squash) * 0.8
            yScale: pet.squash
        }

        // patitas
        Repeater {
            model: [0.2, 0.34, 0.6, 0.74]
            Rectangle {
                x: pet.s * modelData; y: pet.s * 0.72
                width: pet.s * 0.07; height: pet.s * 0.14; radius: pet.s * 0.02
                color: Qt.darker(pet.bodyColor, 1.15)
            }
        }
        // bracitos (el derecho saluda cuando te espera)
        Rectangle {
            x: pet.s * 0.04; y: pet.s * 0.44
            width: pet.s * 0.11; height: pet.s * 0.13; radius: pet.s * 0.03
            color: pet.bodyColor
        }
        Rectangle {
            x: pet.s * 0.85; y: pet.s * 0.44
            width: pet.s * 0.11; height: pet.s * 0.13; radius: pet.s * 0.03
            color: pet.bodyColor
            transformOrigin: Item.BottomLeft
            SequentialAnimation on rotation {
                running: pet.mood === "waiting" || pet.mood === "celebrate"
                loops: Animation.Infinite
                NumberAnimation { to: -55; duration: 200; easing.type: Easing.OutQuad }
                NumberAnimation { to: -15; duration: 200; easing.type: Easing.InOutQuad }
            }
        }
        // cuerpo
        Rectangle {
            id: body
            x: pet.s * 0.13; y: pet.s * 0.28
            width: pet.s * 0.74; height: pet.s * 0.46
            radius: pet.s * 0.1
            color: pet.bodyColor
            Behavior on color { ColorAnimation { duration: 300 } }
            Rectangle {       // brillo
                x: parent.width * 0.08; y: parent.height * 0.1
                width: parent.width * 0.25; height: parent.height * 0.12; radius: height / 2
                color: "#40FFFFFF"
            }
            // mejillas
            Repeater {
                model: [0.12, 0.74]
                Rectangle {
                    visible: pet.joyful
                    x: body.width * modelData; y: body.height * 0.62
                    width: body.width * 0.14; height: body.height * 0.1; radius: height / 2
                    color: "#55FF6F91"
                }
            }
            // ojos
            Repeater {
                model: [0.3, 0.62]
                Item {
                    x: body.width * modelData + pet.look * pet.s * 0.025
                    y: body.height * 0.3 - pet.lookUp * pet.s * 0.03
                    width: pet.s * 0.08; height: pet.s * 0.15
                    Rectangle {
                        visible: !pet.joyful
                        anchors.centerIn: parent
                        width: parent.width * (pet.eyeOpen > 1 ? 1.2 : 1)
                        height: pet.blink ? pet.s * 0.022 : Math.max(pet.s * 0.022, parent.height * Math.min(pet.eyeOpen, 1.15))
                        radius: Math.min(width, height) / 2
                        color: pet.eyeColor
                        Behavior on height { NumberAnimation { duration: 90 } }
                    }
                    Shape {          // ojos felices ^ ^
                        visible: pet.joyful
                        anchors.centerIn: parent
                        width: pet.s * 0.12; height: pet.s * 0.08
                        preferredRendererType: Shape.CurveRenderer
                        ShapePath {
                            fillColor: "transparent"; strokeColor: pet.eyeColor
                            strokeWidth: pet.s * 0.035
                            capStyle: ShapePath.RoundCap; joinStyle: ShapePath.RoundJoin
                            PathSvg {
                                path: "M " + 0 + " " + pet.s * 0.07 + " L " + pet.s * 0.06 + " " + pet.s * 0.015
                                    + " L " + pet.s * 0.12 + " " + pet.s * 0.07
                            }
                        }
                    }
                }
            }
            // boca: sonrisa (feliz) / masticando (comer) / "o" (preocupado)
            Shape {
                visible: pet.joyful && pet.mood !== "eat"
                x: body.width * 0.42; y: body.height * 0.66
                width: body.width * 0.16; height: body.height * 0.12
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    fillColor: "transparent"; strokeColor: pet.eyeColor; strokeWidth: pet.s * 0.025
                    capStyle: ShapePath.RoundCap
                    PathSvg { path: "M 0 0 Q " + body.width * 0.08 + " " + body.height * 0.12 + " " + body.width * 0.16 + " 0" }
                }
            }
            Rectangle {
                readonly property bool speaking: pet.talking && !pet.joyful && pet.mood !== "eat"
                visible: pet.mood === "eat" || pet.mood === "worried" || speaking
                anchors.horizontalCenter: parent.horizontalCenter
                y: body.height * 0.66
                width: body.width * (pet.mood === "eat" ? 0.14 : speaking ? 0.11 : 0.08)
                height: Math.max(pet.s * 0.02, body.height * (pet.mood === "eat" ? 0.16 * pet.chomp
                                                           : speaking ? 0.12 * pet.chomp : 0.1))
                radius: width / 2
                color: pet.eyeColor
            }
        }
        // accesorio (se mueve con el cuerpo)
        Accessory {
            kind: pet.accessory
            scale: pet.s / 100
            transformOrigin: Item.TopLeft
        }
    }

    // ===================== emotes =====================
    // ! y ? (globo de color)
    Rectangle {
        visible: pet.emote === "!" || pet.emote === "?"
        x: pet.s * 0.72; y: pet.hop * 0.5
        width: pet.s * 0.24; height: width; radius: width / 2
        color: pet.emote === "!" ? "#FF9F0A" : "#64D2FF"
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            anchors.centerIn: parent
            text: pet.emote
            color: "black"; font.bold: true; font.pixelSize: pet.s * 0.17
        }
        SequentialAnimation on scale {
            running: pet.emote === "!" || pet.emote === "?"; loops: Animation.Infinite
            NumberAnimation { to: 1.15; duration: 320; easing.type: Easing.OutQuad }
            NumberAnimation { to: 1.0; duration: 320; easing.type: Easing.InQuad }
        }
    }
    // gota de sudor
    Shape {
        id: sweat
        visible: pet.emote === "sweat"
        x: pet.s * 0.8; width: pet.s * 0.1; height: pet.s * 0.15
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: "#8FD3FF"; strokeColor: "#5AB8F0"; strokeWidth: 1
            PathSvg {
                path: "M " + sweat.width / 2 + " 0 Q " + sweat.width + " " + sweat.height * 0.6 + " " + sweat.width / 2 + " " + sweat.height
                    + " Q 0 " + sweat.height * 0.6 + " " + sweat.width / 2 + " 0 Z"
            }
        }
        SequentialAnimation on y {
            running: sweat.visible; loops: Animation.Infinite
            NumberAnimation { from: pet.s * 0.22; to: pet.s * 0.34; duration: 900; easing.type: Easing.InQuad }
            PauseAnimation { duration: 300 }
        }
        SequentialAnimation on opacity {
            running: sweat.visible; loops: Animation.Infinite
            NumberAnimation { from: 1; to: 0; duration: 900; easing.type: Easing.InQuad }
            PauseAnimation { duration: 300 }
        }
    }
    // corazones que suben
    Repeater {
        model: 2
        Shape {
            id: heart
            visible: pet.emote === "heart"
            width: pet.s * 0.16; height: pet.s * 0.15
            x: pet.s * (0.68 + index * 0.12)
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                fillColor: "#FF5A7A"; strokeColor: "transparent"
                PathSvg {
                    path: "M " + heart.width / 2 + " " + heart.height
                        + " C " + -heart.width * 0.1 + " " + heart.height * 0.5 + " " + heart.width * 0.1 + " " + -heart.height * 0.1 + " " + heart.width / 2 + " " + heart.height * 0.28
                        + " C " + heart.width * 0.9 + " " + -heart.height * 0.1 + " " + heart.width * 1.1 + " " + heart.height * 0.5 + " " + heart.width / 2 + " " + heart.height + " Z"
                }
            }
            SequentialAnimation on y {
                running: heart.visible; loops: Animation.Infinite
                PauseAnimation { duration: index * 450 }
                NumberAnimation { from: pet.s * 0.3; to: -pet.s * 0.05; duration: 1100; easing.type: Easing.OutQuad }
            }
            SequentialAnimation on opacity {
                running: heart.visible; loops: Animation.Infinite
                PauseAnimation { duration: index * 450 }
                NumberAnimation { from: 1; to: 0; duration: 1100; easing.type: Easing.InQuad }
            }
        }
    }
    // pensando: globo con tres puntos
    Rectangle {
        visible: pet.emote === "dots"
        x: pet.s * 0.66; y: -pet.s * 0.02
        width: pet.s * 0.34; height: pet.s * 0.18; radius: height / 2
        color: "#E6FFFFFF"
        Rectangle { x: -parent.height * 0.25; y: parent.height * 0.85; width: parent.height * 0.3; height: width; radius: width / 2; color: "#E6FFFFFF" }
        Row {
            anchors.centerIn: parent
            spacing: pet.s * 0.03
            Repeater {
                model: 3
                Rectangle {
                    width: pet.s * 0.045; height: width; radius: width / 2
                    color: "#55555A"
                    SequentialAnimation on opacity {
                        running: pet.emote === "dots"; loops: Animation.Infinite
                        PauseAnimation { duration: index * 180 }
                        NumberAnimation { to: 0.25; duration: 300 }
                        NumberAnimation { to: 1; duration: 300 }
                        PauseAnimation { duration: (2 - index) * 180 }
                    }
                }
            }
        }
    }
    // con hambre: globo con una manzana
    Rectangle {
        visible: pet.emote === "food" && pet.mood === "hungry"
        x: pet.s * 0.66; y: -pet.s * 0.04
        width: pet.s * 0.28; height: width; radius: width / 2
        color: "#E6FFFFFF"
        Rectangle { x: -parent.height * 0.12; y: parent.height * 0.82; width: parent.height * 0.22; height: width; radius: width / 2; color: "#E6FFFFFF" }
        FoodIcon { anchors.centerIn: parent; kind: "apple"; size: pet.s * 0.18 }
    }
    // comiendo: la comida frente a la boca
    FoodIcon {
        visible: pet.mood === "eat"
        x: pet.s * 0.4; y: pet.s * 0.56 + pet.hop
        kind: "cookie"; size: pet.s * 0.2
        opacity: 0.9
    }
    // zZ
    Repeater {
        model: 2
        Text {
            textFormat: Text.PlainText   // nunca interpretar HTML del contenido
            visible: pet.emote === "zz"
            x: pet.s * (0.72 + index * 0.1)
            text: "z"
            color: T.text2
            font.pixelSize: pet.s * (0.16 + index * 0.06); font.bold: true
            SequentialAnimation on y {
                running: pet.emote === "zz"; loops: Animation.Infinite
                PauseAnimation { duration: index * 800 }
                NumberAnimation { from: pet.s * 0.25; to: -pet.s * 0.02; duration: 1600; easing.type: Easing.OutSine }
            }
            SequentialAnimation on opacity {
                running: pet.emote === "zz"; loops: Animation.Infinite
                PauseAnimation { duration: index * 800 }
                NumberAnimation { from: 1; to: 0; duration: 1600 }
            }
        }
    }
    // destello de 4 puntas
    Shape {
        id: sparkle
        visible: pet.emote === "sparkle"
        x: pet.s * 0.78; y: pet.s * 0.04
        width: pet.s * 0.18; height: width
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: "#FFD60A"; strokeColor: "transparent"
            PathSvg {
                property real w: sparkle.width
                path: "M " + w / 2 + " 0 Q " + w * 0.58 + " " + w * 0.42 + " " + w + " " + w / 2
                    + " Q " + w * 0.58 + " " + w * 0.58 + " " + w / 2 + " " + w
                    + " Q " + w * 0.42 + " " + w * 0.58 + " 0 " + w / 2
                    + " Q " + w * 0.42 + " " + w * 0.42 + " " + w / 2 + " 0 Z"
            }
        }
        SequentialAnimation on scale {
            running: sparkle.visible; loops: Animation.Infinite
            NumberAnimation { to: 0.6; duration: 420; easing.type: Easing.InOutSine }
            NumberAnimation { to: 1.1; duration: 420; easing.type: Easing.InOutSine }
        }
    }
    // confeti
    Repeater {
        model: 14
        Rectangle {
            id: bit
            visible: pet.emote === "confetti"
            readonly property var colors: ["#FF5A7A", "#FFD60A", "#64D2FF", "#30D158", "#BF5AF2", "#FF9F0A"]
            width: pet.s * 0.05; height: pet.s * 0.08; radius: 1
            color: colors[index % colors.length]
            x: pet.s * (0.05 + (index * 37 % 90) / 100)
            SequentialAnimation on y {
                running: bit.visible; loops: Animation.Infinite
                PauseAnimation { duration: (index * 173) % 700 }
                NumberAnimation { from: -pet.s * 0.1; to: pet.s * 0.85; duration: 1300 + (index * 91) % 500; easing.type: Easing.InQuad }
            }
            NumberAnimation on rotation {
                running: bit.visible; loops: Animation.Infinite
                from: 0; to: index % 2 ? 360 : -360; duration: 900
            }
        }
    }
}
