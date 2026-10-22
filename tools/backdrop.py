"""Fondo de prueba colorido para revisar el efecto de vidrio sin capturar otras apps."""
import sys

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QRadialGradient
from PySide6.QtWidgets import QApplication, QWidget


class Backdrop(QWidget):
    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#1b2a4a"))
        w, h = self.width(), self.height()
        for (fx, fy, r, c) in [(0.85, 0.15, 0.35, "#ff6b6b"), (0.7, 0.55, 0.4, "#4ecdc4"),
                               (0.15, 0.8, 0.45, "#ffd93d"), (0.35, 0.3, 0.3, "#a66cff"),
                               (0.95, 0.85, 0.3, "#ff9f1c")]:
            g = QRadialGradient(QPointF(fx * w, fy * h), r * w)
            g.setColorAt(0, QColor(c))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            p.fillRect(self.rect(), g)
        p.setPen(QColor(255, 255, 255, 200))
        p.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        for y in range(40, h, 70):
            p.drawText(20, y, "Texto de prueba detrás del vidrio · Lorem ipsum dolor sit amet " * 3)


app = QApplication(sys.argv)
win = Backdrop()
win.setWindowFlags(Qt.WindowType.FramelessWindowHint)
win.setGeometry(app.primaryScreen().geometry())
win.show()
sys.exit(app.exec())
