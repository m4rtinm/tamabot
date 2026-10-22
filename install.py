#!/usr/bin/env python3
"""Instala (o desinstala con --uninstall) Claude Tray.

- Agrega los hooks y la status line a ~/.claude/settings.json (con respaldo).
  Tus hooks existentes se conservan; solo se tocan las entradas de Claude Tray.
- Crea el lanzador ~/.local/bin/claude-tray, la entrada de menu y el autoarranque.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
SETTINGS = HOME / ".claude" / "settings.json"
CONFIG_DIR = HOME / ".config" / "claude-tray"
CONFIG = CONFIG_DIR / "config.json"
BIN = HOME / ".local" / "bin" / "claude-tray"
DESKTOP = HOME / ".local" / "share" / "applications" / "claude-tray.desktop"
AUTOSTART = HOME / ".config" / "autostart" / "claude-tray.desktop"
ICON = HOME / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "claude-tray.png"

PY = "/usr/bin/python3"
HOOK = f"{PY} -I -S {ROOT / 'hook' / 'ctray_hook.py'}"
STATUS = f"{PY} -I -S {ROOT / 'hook' / 'ctray_statusline.py'}"
MARK = "ctray_"            # identifica nuestras entradas en settings.json
ASYNC_EVENTS = ["SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse",
                "PostToolUse", "Notification", "Stop", "StopFailure"]


def load_settings():
    try:
        return json.loads(SETTINGS.read_text())
    except FileNotFoundError:
        return {}


def save_settings(data):
    if SETTINGS.exists():
        stamp, n = time.strftime("%Y%m%d-%H%M%S"), 0
        backup = SETTINGS.with_name(f"settings.json.bak-claude-tray-{stamp}")
        while backup.exists():
            n += 1
            backup = SETTINGS.with_name(f"settings.json.bak-claude-tray-{stamp}-{n}")
        shutil.copy2(SETTINGS, backup)
        print(f"  respaldo: {backup}")
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def strip_ours(hooks):
    """Quita las entradas de Claude Tray sin tocar las demas."""
    for event in list(hooks):
        groups = []
        for group in hooks[event]:
            kept = [h for h in group.get("hooks", []) if MARK not in h.get("command", "")]
            if kept:
                groups.append({**group, "hooks": kept})
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    return hooks


def load_config():
    try:
        return json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")


def install():
    venv_py = ROOT / ".venv" / "bin" / "python"
    if not venv_py.exists():
        sys.exit("Falta el entorno .venv (ver README: uv venv --python 3.12 .venv && uv pip install PySide6-Essentials)")

    print("Configurando Claude Code…")
    data = load_settings()
    hooks = strip_ours(data.get("hooks", {}))
    hooks.setdefault("PermissionRequest", []).append(
        {"matcher": "*", "hooks": [{"type": "command", "command": HOOK, "timeout": 600}]})
    # Preguntas con opciones: PreToolUse sincrono solo para AskUserQuestion
    hooks.setdefault("PreToolUse", []).append(
        {"matcher": "AskUserQuestion", "hooks": [{"type": "command", "command": HOOK + " --ask", "timeout": 600}]})
    for ev in ASYNC_EVENTS:
        hooks.setdefault(ev, []).append({"hooks": [{"type": "command", "command": HOOK, "async": True, "timeout": 5}]})
    data["hooks"] = hooks

    cfg = load_config()
    current = data.get("statusLine")
    if current and MARK not in current.get("command", ""):
        cfg["statusline_chain"] = current.get("command")
        print(f"  tu status line actual se encadena: {cfg['statusline_chain']}")
    data["statusLine"] = {"type": "command", "command": STATUS, "padding": 0}
    save_settings(data)
    cfg.setdefault("approval_timeout", 540)
    cfg.setdefault("notify_done", True)
    save_config(cfg)

    print("Creando lanzador, menú y autoarranque…")
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.write_text(f'#!/usr/bin/env bash\ncd "{ROOT}"\nexec "{venv_py}" -m claudetray "$@"\n')
    BIN.chmod(0o755)
    ICON.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(venv_py), "-c", f"from PySide6.QtGui import QGuiApplication; app = QGuiApplication([]);"
                    f"from claudetray.icon import save_png; save_png({str(ICON)!r})"],
                   cwd=ROOT, env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}, check=False)
    entry = (
        "[Desktop Entry]\nType=Application\nName=Claude Tray\n"
        "Comment=Aprueba solicitudes y sigue tus sesiones de Claude Code desde la bandeja\n"
        f"Exec={BIN}\nIcon={ICON}\nTerminal=false\nCategories=Development;Utility;\n"
        "StartupNotify=false\nX-KDE-autostart-after=panel\n"
    )
    DESKTOP.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP.write_text(entry)
    AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
    AUTOSTART.write_text(entry)
    print("\nListo. Ejecuta 'claude-tray' (o búscalo en el menú). Se abrirá solo al iniciar sesión.")
    print("Las sesiones de Claude Code ya abiertas toman los hooks nuevos al reiniciarse.")


def uninstall():
    print("Quitando hooks y status line de Claude Tray…")
    data = load_settings()
    if "hooks" in data:
        data["hooks"] = strip_ours(data["hooks"])
        if not data["hooks"]:
            del data["hooks"]
    cfg = load_config()
    if MARK in (data.get("statusLine") or {}).get("command", ""):
        chain = cfg.get("statusline_chain")
        if chain:
            data["statusLine"] = {"type": "command", "command": chain}
        else:
            del data["statusLine"]
    save_settings(data)
    for path in (BIN, DESKTOP, AUTOSTART, ICON):
        if path.exists():
            path.unlink()
    print("Listo. (La carpeta del proyecto y ~/.config/claude-tray quedan intactas.)")


if __name__ == "__main__":
    uninstall() if "--uninstall" in sys.argv else install()
