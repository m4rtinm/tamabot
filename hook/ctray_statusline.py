#!/usr/bin/env python3
"""Status line de Claude Code que ademas reenvia los datos a Claude Tray.

Claude Code solo entrega el uso del plan (rate_limits) a la status line,
asi que este script es la fuente del consumo en tiempo real. Si en la
config hay un "statusline_chain", se ejecuta ese comando y se muestra su
salida en lugar de la linea por defecto.
"""
import json
import os
import socket
import subprocess
import sys
import time

_XDG = os.environ.get("XDG_RUNTIME_DIR")
RUNTIME = _XDG if _XDG and os.path.isdir(_XDG) else f"/tmp/claude-tray-{os.getuid()}"   # igual que la app
SOCK = os.path.join(RUNTIME, "claude-tray.sock")
CONFIG = os.path.join(os.path.expanduser("~"), ".config", "claude-tray", "config.json")

DIM, RESET = "\033[2m", "\033[0m"
ORANGE, AMBER, RED = "\033[38;5;173m", "\033[38;5;214m", "\033[38;5;203m"


def forward(raw):
    if RUNTIME != _XDG:
        try:
            st = os.lstat(RUNTIME)
            if os.path.islink(RUNTIME) or st.st_uid != os.getuid() or st.st_mode & 0o077:
                return
        except OSError:
            return
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.3)
        s.connect(SOCK)
        s.sendall((json.dumps({"kind": "status", "ppid": os.getppid(), "data": json.loads(raw)}) + "\n").encode())
        s.close()
    except (OSError, ValueError):
        pass


def chained(raw):
    try:
        with open(CONFIG) as f:
            cmd = json.load(f).get("statusline_chain")
    except Exception:
        cmd = None
    if not cmd:
        return None
    try:
        return subprocess.run(cmd, shell=True, input=raw, capture_output=True, text=True, timeout=5).stdout.rstrip("\n")
    except Exception:
        return None


def pct_color(p):
    return RED if p >= 90 else AMBER if p >= 70 else ORANGE


def fmt_left(epoch):
    secs = max(0, int(epoch - time.time()))
    h, m = divmod(secs // 60, 60)
    return f"{h}h{m:02d}" if h else f"{m}m"


def default_line(d):
    parts = []
    model = (d.get("model") or {}).get("display_name")
    if model:
        parts.append(model)
    ctx = (d.get("context_window") or {}).get("used_percentage")
    if ctx is not None:
        parts.append(f"ctx {round(ctx)}%")
    rl = d.get("rate_limits") or {}
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        w = rl.get(key)
        if w and w.get("used_percentage") is not None:
            p = w["used_percentage"]
            txt = f"{label} {pct_color(p)}{round(p)}%{RESET}{DIM}"
            if key == "five_hour" and w.get("resets_at"):
                txt += f" ({fmt_left(w['resets_at'])})"
            parts.append(txt)
    return f"{DIM}" + " · ".join(parts) + RESET


def main():
    raw = sys.stdin.read()
    forward(raw)
    line = chained(raw)
    if line is None:
        try:
            line = default_line(json.loads(raw))
        except ValueError:
            line = ""
    print(line)


if __name__ == "__main__":
    main()
