"""Desenfoque real detras de la ventana usando el efecto Blur de KWin (X11).

La region se escribe directamente con libX11: xprop solo acepta 64 valores
y una region de esquinas redondeadas necesita bastantes mas.
"""
import ctypes
import ctypes.util
import math
import struct

from PySide6.QtGui import QMatrix4x4

ATOM = b"_KDE_NET_WM_BLUR_BEHIND_REGION"
CONTRAST_ATOM = b"_KDE_NET_WM_BACKGROUND_CONTRAST_REGION"
XA_CARDINAL = 6
PROP_MODE_REPLACE = 0

_x11 = None
_display = None
_atom = None
_contrast_atom = None


def _init():
    global _x11, _display, _atom, _contrast_atom
    if _display is not None:
        return True
    path = ctypes.util.find_library("X11")
    if not path:
        return False
    _x11 = ctypes.cdll.LoadLibrary(path)
    _x11.XOpenDisplay.restype = ctypes.c_void_p
    _x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    _x11.XInternAtom.restype = ctypes.c_ulong
    _x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    _x11.XChangeProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong,
                                     ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    _x11.XFlush.argtypes = [ctypes.c_void_p]
    _display = _x11.XOpenDisplay(None)
    if not _display:
        return False
    _atom = _x11.XInternAtom(_display, ATOM, 0)
    _contrast_atom = _x11.XInternAtom(_display, CONTRAST_ATOM, 0)
    return True


def color_matrix(contrast, intensity, saturation):
    """Misma matriz que KWindowEffects::enableBackgroundContrast (columna mayor, en uint32)."""
    rv, gv, bv = ((1.0 - saturation) * k for k in (0.2126, 0.7152, 0.0722))
    sat = QMatrix4x4(rv + saturation, rv, rv, 0.0,
                     gv, gv + saturation, gv, 0.0,
                     bv, bv, bv + saturation, 0.0,
                     0.0, 0.0, 0.0, 1.0)
    inten = QMatrix4x4()
    inten.scale(intensity, intensity, intensity)
    t = (1.0 - contrast) / 2.0
    cont = QMatrix4x4(contrast, 0.0, 0.0, 0.0,
                      0.0, contrast, 0.0, 0.0,
                      0.0, 0.0, contrast, 0.0,
                      t, t, t, 1.0)
    m = (cont * sat * inten).transposed()
    return [struct.unpack("I", struct.pack("f", v))[0] for v in m.copyDataTo()]


def rounded_region(x, y, w, h, r):
    """Aproxima un rectangulo redondeado con franjas (KWin solo acepta rectangulos)."""
    r = max(0, min(r, w // 2, h // 2))
    insets = []
    for i in range(r):
        dy = r - i - 0.5
        insets.append(int(round(r - math.sqrt(max(0.0, r * r - dy * dy)))))
    rects, i = [], 0
    while i < r:                          # agrupa filas con el mismo margen
        j = i
        while j + 1 < r and insets[j + 1] == insets[i]:
            j += 1
        n = j - i + 1
        rects.append((x + insets[i], y + i, w - 2 * insets[i], n))
        rects.append((x + insets[i], y + h - i - n, w - 2 * insets[i], n))
        i = j + 1
    rects.append((x, y + r, w, h - 2 * r))
    return rects


def tail_region(x, y, w, h, tail_x, size, direction):
    """Franjas del pico de la burbuja (direction 1 = abajo, -1 = arriba)."""
    rects = []
    for i in range(0, size, 2):
        half = max(1, int(round(size * (1 - (i + 1) / size))))
        top = y + h + i if direction == 1 else y - i - 2
        rects.append((x + tail_x - half, top, 2 * half, 2))
    return rects


def apply(window, x, y, w, h, radius, tail_x=0, tail_size=0, tail_dir=0, vibrancy=(0.9, 1.0, 1.8)):
    if w <= 0 or h <= 0 or not _init():
        return
    dpr = window.devicePixelRatio()
    s = lambda v: int(round(v * dpr))
    rects = rounded_region(s(x), s(y), s(w), s(h), s(radius))
    if tail_dir and tail_size:
        tx = min(max(tail_x, radius + tail_size + 2), w - radius - tail_size - 2)
        rects += tail_region(s(x), s(y), s(w), s(h), s(tx), s(tail_size), int(tail_dir))
    values = [v for rect in rects for v in rect]
    # Xlib usa 'long' para los elementos de formato 32.
    data = (ctypes.c_long * len(values))(*values)
    wid = int(window.winId())
    _x11.XChangeProperty(_display, wid, _atom, XA_CARDINAL, 32, PROP_MODE_REPLACE, data, len(values))
    if vibrancy:   # saturacion extra del fondo, como el "vibrancy" de macOS
        cvals = values + color_matrix(*vibrancy)
        cdata = (ctypes.c_long * len(cvals))(*cvals)
        _x11.XChangeProperty(_display, wid, _contrast_atom, XA_CARDINAL, 32, PROP_MODE_REPLACE, cdata, len(cvals))
    _x11.XFlush(_display)
