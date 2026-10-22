"""Iconos de la bandeja: la mascota animada, o un anillo simple que gira mientras hay trabajo."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

ORANGE = QColor("#D97757")
BADGE = QColor("#FF9F0A")
RAYS = 12


def paint_glyph(p, cx, cy, size, angle=0.0, color=ORANGE):
    """Icono simple: un anillo; mientras hay trabajo, un arco recorre el anillo."""
    track = QColor(color)
    track.setAlphaF(0.35)
    w = size * 0.12
    r = size * 0.34
    rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(track, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawEllipse(rect)
    p.setPen(QPen(color, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawArc(rect, int((90 - angle) * 16), int(-110 * 16))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawEllipse(QPointF(cx, cy), size * 0.09, size * 0.09)


def tray_icon(angle=0.0, badge=False, dim=False, size=64, muted=False):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor(ORANGE)
    if dim:
        color.setAlphaF(0.55)
    paint_glyph(p, size / 2, size / 2, size, angle, color)
    if badge:
        d = size * 0.38
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawEllipse(QPointF(size - d / 2, d / 2), d / 2 + size * 0.04, d / 2 + size * 0.04)
        p.setBrush(BADGE)
        p.drawEllipse(QPointF(size - d / 2, d / 2), d / 2, d / 2)
    if muted:
        paint_muted(p, size)
    p.end()
    return QIcon(pm)


def save_png(path, size=256):
    pet_icon("idle", 1, size=size).pixmap(size, size).save(str(path))


def paint_muted(p, size):
    """Circulo gris con una raya en la esquina inferior: avisos silenciados."""
    u = size / 64
    c = QPointF(size - 12 * u, size - 12 * u)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 110))
    p.drawEllipse(c, 12 * u, 12 * u)
    p.setBrush(QColor("#8E8E93"))
    p.drawEllipse(c, 10 * u, 10 * u)
    p.setPen(QPen(QColor("white"), 3 * u, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(c.x() - 5 * u, c.y() - 5 * u), QPointF(c.x() + 5 * u, c.y() + 5 * u))


JOYFUL = {"happy", "celebrate", "love", "play", "eat"}
HALF_EYES = {"tired": 4, "bored": 5, "hungry": 8}


def paint_emote(p, emote, phase, size):
    """Emote pequeño arriba a la derecha del icono."""
    u = size / 64
    c = QPointF(size - 11 * u, 11 * u)
    pulse = 1.0 if phase % 2 == 0 else 0.88
    p.setPen(Qt.PenStyle.NoPen)
    if emote in ("!", "?"):
        r = 11 * u * pulse
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawEllipse(c, r + 1.5 * u, r + 1.5 * u)
        p.setBrush(BADGE if emote == "!" else QColor("#64D2FF"))
        p.drawEllipse(c, r, r)
        p.setPen(QColor("black"))
        f = p.font(); f.setPixelSize(int(17 * u)); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), Qt.AlignmentFlag.AlignCenter, emote)
    elif emote == "sweat":
        y = (4 + phase % 4 * 2) * u
        path = QPainterPath(QPointF(c.x(), y))
        path.quadTo(QPointF(c.x() + 7 * u, y + 10 * u), QPointF(c.x(), y + 14 * u))
        path.quadTo(QPointF(c.x() - 7 * u, y + 10 * u), QPointF(c.x(), y))
        p.setBrush(QColor("#8FD3FF"))
        p.drawPath(path)
    elif emote == "heart":
        y = (2 - phase % 3) * u
        path = QPainterPath(QPointF(c.x(), y + 18 * u))
        path.cubicTo(QPointF(c.x() - 13 * u, y + 9 * u), QPointF(c.x() - 7 * u, y - 1 * u), QPointF(c.x(), y + 5 * u))
        path.cubicTo(QPointF(c.x() + 7 * u, y - 1 * u), QPointF(c.x() + 13 * u, y + 9 * u), QPointF(c.x(), y + 18 * u))
        p.setBrush(QColor("#FF5A7A"))
        p.drawPath(path)
    elif emote == "dots":
        p.setBrush(QColor(255, 255, 255, 235))
        p.drawRoundedRect(QRectF(size - 26 * u, 2 * u, 24 * u, 13 * u), 6.5 * u, 6.5 * u)
        for i in range(3):
            p.setBrush(QColor("#55555A") if (phase % 3) == i else QColor("#A0A0A6"))
            p.drawEllipse(QPointF(size - 20 * u + i * 6 * u, 8.5 * u), 2.2 * u, 2.2 * u)
    elif emote == "food":
        p.setBrush(QColor("#E5484D"))
        p.drawEllipse(c, 8 * u * pulse, 8 * u * pulse)
        p.setBrush(QColor("#5BC85B"))
        p.drawEllipse(QPointF(c.x() + 3 * u, c.y() - 8 * u), 3 * u, 2 * u)
    elif emote in ("sparkle", "confetti"):
        r = 9 * u * pulse
        path = QPainterPath(QPointF(c.x(), c.y() - r))
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            path.quadTo(c, QPointF(c.x() + dx * r, c.y() + dy * r))
        p.setBrush(QColor("#FFD60A"))
        p.drawPath(path)
        if emote == "confetti":
            for i, col in enumerate(("#FF5A7A", "#64D2FF", "#30D158")):
                p.setBrush(QColor(col))
                p.drawRect(QRectF((8 + i * 14) * u, ((phase * 3 + i * 7) % 14) * u, 3 * u, 4 * u))
    elif emote == "zz":
        p.setPen(QColor(200, 200, 210))
        f = p.font(); f.setPixelSize(int(16 * u)); f.setBold(True); p.setFont(f)
        p.drawText(QPointF(48 * u, (14 - phase % 3 * 2) * u), "z")


def pet_icon(mood="idle", phase=0, color="#D97757", size=64, muted=False, emote=""):
    """Mascota en miniatura para la bandeja. phase avanza con el temporizador de animacion."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    u = size / 64
    body = QColor(color)
    if mood == "sleep":
        body.setAlphaF(0.6)
    dark = QColor("#2B1D17")
    dy = 0
    if mood in ("working", "thinking"):
        dy = (0, -2, -3, -2)[phase % 4] * u
    elif mood in ("happy", "love", "eat"):
        dy = (0, -6, -9, -6, 0, 0, 0, 0)[phase % 8] * u
    elif mood in ("celebrate", "play"):
        dy = (0, -8, -12, -8, 0, -4)[phase % 6] * u
    elif mood == "tired":
        dy = 2 * u
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(body.darker(115))
    for lx in (13, 22, 38, 47):                       # patitas
        p.drawRoundedRect(QRectF(lx * u, 46 * u + dy, 5 * u, 10 * u), 1.5 * u, 1.5 * u)
    p.setBrush(body)
    p.drawRoundedRect(QRectF(2 * u, 28 * u + dy, 8 * u, 9 * u), 2 * u, 2 * u)   # bracitos
    arm_up = mood in ("waiting", "celebrate") and phase % 2 == 0
    p.drawRoundedRect(QRectF(54 * u, (22 if arm_up else 28) * u + dy, 8 * u, 9 * u), 2 * u, 2 * u)
    p.drawRoundedRect(QRectF(8 * u, 16 * u + dy, 48 * u, 32 * u), 7 * u, 7 * u)  # cuerpo
    p.setBrush(dark)
    look = (-2, -2, 2, 2)[phase % 4] * u if mood == "working" else 3 * u if mood == "bored" else 0
    up = -3 * u if mood == "thinking" else 0
    for ex in (22, 38):                               # ojos
        cx = ex * u + look
        if mood in JOYFUL:
            p.setPen(QPen(dark, 3.2 * u, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPolyline([QPointF(cx - 4 * u, 33 * u + dy), QPointF(cx, 28 * u + dy), QPointF(cx + 4 * u, 33 * u + dy)])
            p.setPen(Qt.PenStyle.NoPen)
        elif mood == "sleep" or (mood == "idle" and phase % 24 == 0):
            p.drawRoundedRect(QRectF(cx - 3 * u, 30 * u + dy, 6 * u, 2.4 * u), 1 * u, 1 * u)
        else:
            h = HALF_EYES.get(mood, 12 if mood in ("waiting", "worried") else 10)
            p.drawRoundedRect(QRectF(cx - 2.6 * u, (31 - h / 2) * u + dy + up, 5.2 * u, h * u), 2.6 * u, 2.6 * u)
    if mood == "eat":                                 # boca masticando
        h = (5 if phase % 2 == 0 else 1.5) * u
        p.drawRoundedRect(QRectF(29 * u, 40 * u + dy, 6 * u, h), 2 * u, 2 * u)
    if emote:
        paint_emote(p, emote, phase, size)
    if muted:
        paint_muted(p, size)
    p.end()
    return QIcon(pm)
