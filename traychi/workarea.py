"""Area util de cada pantalla descontando los paneles de Plasma.

Con varios monitores en X11, Qt devuelve availableGeometry() igual a la
pantalla completa, asi que se calcula a partir de _NET_WM_STRUT_PARTIAL
de las ventanas tipo DOCK.
"""
import re
import shutil
import subprocess
import time

from PySide6.QtCore import QRect

XPROP = shutil.which("xprop")
_cache = {"at": 0.0, "struts": []}


def _xprop(*args):
    try:
        return subprocess.run([XPROP, *args], capture_output=True, text=True, timeout=1).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _struts():
    if not XPROP:
        return []
    if time.monotonic() - _cache["at"] < 10:
        return _cache["struts"]
    out = []
    ids = re.findall(r"0x[0-9a-f]+", _xprop("-root", "_NET_CLIENT_LIST"))
    for wid in ids:
        text = _xprop("-id", wid, "_NET_WM_WINDOW_TYPE", "_NET_WM_STRUT_PARTIAL")
        if "_NET_WM_WINDOW_TYPE_DOCK" not in text:
            continue
        m = re.search(r"_NET_WM_STRUT_PARTIAL\(CARDINAL\) = ([\d, ]+)", text)
        if m:
            vals = [int(v) for v in m.group(1).split(",")]
            if len(vals) == 12:
                out.append(vals)
    _cache.update(at=time.monotonic(), struts=out)
    return out


def available(screen):
    """QRect util de la pantalla (QScreen)."""
    g = screen.geometry()
    virt = screen.virtualGeometry()
    left, top, right, bottom = g.left(), g.top(), g.right(), g.bottom()
    for (sl, sr, st, sb, ly0, ly1, ry0, ry1, tx0, tx1, bx0, bx1) in _struts():
        if sb and bx0 <= g.right() and bx1 >= g.left():
            bottom = min(bottom, virt.bottom() - sb)
        if st and tx0 <= g.right() and tx1 >= g.left():
            top = max(top, virt.top() + st)
        if sl and ly0 <= g.bottom() and ly1 >= g.top():
            left = max(left, virt.left() + sl)
        if sr and ry0 <= g.bottom() and ry1 >= g.top():
            right = min(right, virt.right() - sr)
    return QRect(left, top, right - left + 1, bottom - top + 1)
