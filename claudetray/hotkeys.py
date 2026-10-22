"""Atajos de teclado globales en X11 (XGrabKey), sin configurar nada en el escritorio.

En Wayland no se pueden capturar teclas globales desde una app: ahi se usan los
comandos `claude-tray --allow` / `--deny` / `--panel`, asignados en los ajustes
de teclado del escritorio.
"""
import ctypes
import ctypes.util
import logging
import os
import threading

log = logging.getLogger("claude-tray")

MODS = {"shift": 1, "ctrl": 4, "control": 4, "alt": 8, "super": 64, "meta": 64, "win": 64}
LOCK, NUMLOCK = 2, 16                 # Bloq Mayús y Bloq Num no deben impedir el atajo
KEYPRESS = 2
GRAB_MODE_ASYNC = 1


class XKeyEvent(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong), ("send_event", ctypes.c_int),
                ("display", ctypes.c_void_p), ("window", ctypes.c_ulong), ("root", ctypes.c_ulong),
                ("subwindow", ctypes.c_ulong), ("time", ctypes.c_ulong), ("x", ctypes.c_int),
                ("y", ctypes.c_int), ("x_root", ctypes.c_int), ("y_root", ctypes.c_int),
                ("state", ctypes.c_uint), ("keycode", ctypes.c_uint), ("same_screen", ctypes.c_int)]


class XEvent(ctypes.Union):
    _fields_ = [("type", ctypes.c_int), ("xkey", XKeyEvent), ("pad", ctypes.c_long * 24)]


ERROR_HANDLER = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)


def parse(spec):
    """'Super+Shift+A' -> (mascara de modificadores, nombre de tecla) o None si no se entiende."""
    parts = [p.strip() for p in (spec or "").split("+") if p.strip()]
    if not parts:
        return None
    mask = 0
    for p in parts[:-1]:
        if p.lower() not in MODS:
            return None
        mask |= MODS[p.lower()]
    key = parts[-1]
    return mask, key.lower() if len(key) == 1 else key


def is_x11():
    return os.environ.get("XDG_SESSION_TYPE", "").lower() != "wayland" and not os.environ.get("WAYLAND_DISPLAY")


class GlobalHotkeys:
    """Registra los atajos y llama a on_action(nombre) desde un hilo propio."""

    def __init__(self, bindings, on_action):
        self.bindings = bindings            # {"allow": "Super+Shift+A", ...}
        self.on_action = on_action
        self.active = {}                    # accion -> atajo realmente registrado
        self.failed = {}                    # accion -> motivo
        self._errors = 0
        self._handler = ERROR_HANDLER(self._on_error)   # hay que mantener la referencia viva

    def _on_error(self, _display, _event):
        self._errors += 1                   # p. ej. BadAccess: otra app ya usa ese atajo
        return 0

    def start(self):
        if not is_x11():
            self.failed = {a: "Wayland" for a in self.bindings}
            return False
        path = ctypes.util.find_library("X11")
        if not path:
            self.failed = {a: "sin libX11" for a in self.bindings}
            return False
        x = ctypes.cdll.LoadLibrary(path)
        x.XOpenDisplay.restype = ctypes.c_void_p
        x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x.XDefaultRootWindow.restype = ctypes.c_ulong
        x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x.XStringToKeysym.restype = ctypes.c_ulong
        x.XStringToKeysym.argtypes = [ctypes.c_char_p]
        x.XKeysymToKeycode.restype = ctypes.c_ubyte
        x.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        x.XGrabKey.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_ulong,
                               ctypes.c_int, ctypes.c_int, ctypes.c_int]
        x.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x.XNextEvent.argtypes = [ctypes.c_void_p, ctypes.POINTER(XEvent)]
        x.XSetErrorHandler.argtypes = [ERROR_HANDLER]
        x.XSetErrorHandler(self._handler)
        dpy = x.XOpenDisplay(None)
        if not dpy:
            self.failed = {a: "sin pantalla X" for a in self.bindings}
            return False
        root = x.XDefaultRootWindow(dpy)
        keymap = {}
        for action, spec in self.bindings.items():
            parsed = parse(spec)
            if not parsed:
                self.failed[action] = "atajo no válido"
                continue
            mask, key = parsed
            code = x.XKeysymToKeycode(dpy, x.XStringToKeysym(key.encode()))
            if not code:
                self.failed[action] = "tecla desconocida"
                continue
            before = self._errors
            for extra in (0, LOCK, NUMLOCK, LOCK | NUMLOCK):
                x.XGrabKey(dpy, code, mask | extra, root, 0, GRAB_MODE_ASYNC, GRAB_MODE_ASYNC)
            x.XSync(dpy, 0)
            if self._errors > before:
                self.failed[action] = "otra app ya usa ese atajo"
                continue
            keymap[(code, mask)] = action
            self.active[action] = spec
        if not keymap:
            return False

        def loop():
            ev = XEvent()
            while True:
                x.XNextEvent(dpy, ctypes.byref(ev))
                if ev.type == KEYPRESS:
                    k = ev.xkey
                    action = keymap.get((k.keycode, k.state & ~(LOCK | NUMLOCK)))
                    if action:
                        try:
                            self.on_action(action)
                        except Exception:
                            log.exception("Error en el atajo %s", action)

        threading.Thread(target=loop, daemon=True, name="hotkeys").start()
        log.info("Atajos globales activos: %s", self.active)
        return True
