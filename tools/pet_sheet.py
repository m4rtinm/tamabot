"""Dibuja a la mascota en varios animos y accesorios y guarda una hoja de muestra (para revisar el diseño).

Uso: .venv/bin/python tools/pet_sheet.py salida.png
"""
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView

QML = Path(__file__).resolve().parent.parent / "traychi" / "qml"
CASES = [(d, mood, emote, acc) for d in ("clawd", "mochi") for mood, emote, acc in (
    ("idle", "", ""), ("happy", "sparkle", ""), ("waiting", "!", ""), ("sleep", "zz", ""),
    ("eat", "food", ""), ("worried", "sweat", ""), ("idle", "", "hat"), ("idle", "", "glasses"))]

app = QGuiApplication(sys.argv)
view = QQuickView()
view.engine().rootContext().setContextProperty("T", {"text2": "#aaa"})
view.engine().rootContext().setContextProperty("MONO", "monospace")
src = "import QtQuick\nRectangle { width: 8*190; height: 2*190; color: '#16202e'\n Grid { columns: 8\n"
for design, mood, emote, acc in CASES:
    color = "#D97757" if design == "clawd" else "#F2EAD8"
    src += (f"  Item {{ width: 190; height: 190\n   Pet {{ x: 15; y: 10; s: 160; design: '{design}'; bodyColor: '{color}'; mood: '{mood}'; emote: '{emote}'; accessory: '{acc}' }}\n"
            f"   Text {{ textFormat: Text.PlainText; y: 172; width: 190; horizontalAlignment: Text.AlignHCenter; color: '#9ab'; "
            f"font.pixelSize: 12; text: '{design} · {mood}{(' + ' + acc) if acc else ''}' }} }}\n")
src += " }\n}\n"
tmp = QML / "_sheet.qml"
tmp.write_text(src)
view.setSource(QUrl.fromLocalFile(str(tmp)))
view.show()


def grab():
    view.grabWindow().save(sys.argv[1] if len(sys.argv) > 1 else "pet_sheet.png")
    tmp.unlink()
    app.quit()


QTimer.singleShot(1800, grab)
app.exec()
