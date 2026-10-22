"""Carga unica de libX11, con XInitThreads.

La app usa Xlib desde dos hilos (atajos de teclado y desenfoque) y Qt tambien puede usarlo.
Xlib exige llamar a XInitThreads() antes de cualquier otra llamada; sin eso, el uso desde
varios hilos puede tumbar el proceso de forma esporadica y sin dejar rastro.
"""
import ctypes
import ctypes.util

_lib = None
_tried = False


def lib():
    """libX11 lista para usarse desde varios hilos, o None si no esta disponible."""
    global _lib, _tried
    if not _tried:
        _tried = True
        path = ctypes.util.find_library("X11")
        if path:
            _lib = ctypes.cdll.LoadLibrary(path)
            _lib.XInitThreads()
    return _lib
