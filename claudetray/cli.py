"""Comandos de linea que no necesitan Qt: --version y el control de la app abierta."""
import json
import socket

from . import config

CONTROL_FLAGS = {"--allow": "allow", "--deny": "deny", "--panel": "panel", "--terminal": "terminal"}


def send_control(action):
    """`claude-tray --allow` etc.: le pide la accion a la app abierta por el socket."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(config.SOCKET_PATH)
        s.sendall((json.dumps({"kind": "control", "action": action}) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        reply = json.loads(buf.split(b"\n")[0] or b"{}")
    except (OSError, ValueError):
        print("Claude Tray no está abierto.")
        return 2
    print(reply.get("message", ""))
    return 0 if reply.get("ok") else 1


def handle(argv):
    """Devuelve el codigo de salida si el comando se atendio aqui, o None para abrir la app."""
    if "--version" in argv:
        from . import __version__
        print(f"Claude Tray {__version__}")
        return 0
    for flag, action in CONTROL_FLAGS.items():
        if flag in argv:
            try:
                config.secure_runtime()
            except (RuntimeError, OSError) as exc:
                print(exc)
                return 2
            return send_control(action)
    return None
