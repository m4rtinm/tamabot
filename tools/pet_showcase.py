"""Genera docs/img/mascotas.png: los dos diseños de la mascota en varios ánimos, para el README.

Uso: .venv/bin/python tools/pet_showcase.py
"""
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

ROOT = Path(__file__).resolve().parent.parent
QML = ROOT / "traychi" / "qml"
MOODS = [("idle", "", "tranquila"), ("working", "", "trabajando"), ("waiting", "!", "te espera"),
         ("happy", "sparkle", "feliz"), ("eat", "food", "comiendo"), ("sleep", "zz", "durmiendo")]
DESIGNS = [("clawd", "#D97757", "Clawd · por defecto"), ("mochi", "#F2EAD8", "Mochi")]
W, H, LEFT = 150, 168, 150

app = QGuiApplication(sys.argv)
view = QQuickView()
ctx = view.engine().rootContext()
ctx.setContextProperty("T", {"text2": "#93A3B8"})
ctx.setContextProperty("MONO", "monospace")
src = (f"import QtQuick\nRectangle {{ width: {LEFT + W * len(MOODS) + 20}; height: {H * len(DESIGNS) + 30}\n"
       " gradient: Gradient { GradientStop { position: 0; color: '#132036' } GradientStop { position: 1; color: '#0E1726' } }\n")
for r, (design, color, label) in enumerate(DESIGNS):
    y = 15 + r * H
    src += (f" Text {{ textFormat: Text.PlainText; x: 24; y: {y + 62}; width: {LEFT - 30}; wrapMode: Text.Wrap; "
            f"text: '{label}'; color: '#E9EEF5'; font.pixelSize: 17; font.bold: true }}\n")
    for c, (mood, emote, name) in enumerate(MOODS):
        x = LEFT + c * W
        src += (f" Pet {{ x: {x + 15}; y: {y + 4}; s: 120; design: '{design}'; bodyColor: '{color}'; mood: '{mood}'; emote: '{emote}' }}\n"
                f" Text {{ textFormat: Text.PlainText; x: {x}; y: {y + 132}; width: {W}; horizontalAlignment: Text.AlignHCenter; "
                f"text: '{name}'; color: '#93A3B8'; font.pixelSize: 13 }}\n")
src += "}\n"
tmp = QML / "_showcase.qml"
tmp.write_text(src)
view.setSource(QUrl.fromLocalFile(str(tmp)))
view.show()


def grab():
    out = ROOT / "docs" / "img" / "mascotas.png"
    view.grabWindow().save(str(out))
    tmp.unlink()
    print(out)
    app.quit()


QTimer.singleShot(2200, grab)
app.exec()
