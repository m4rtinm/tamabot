import json
import os
from pathlib import Path

RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/claude-tray-{os.getuid()}")
SOCKET_PATH = str(RUNTIME / "claude-tray.sock")
CONFIG_DIR = Path.home() / ".config" / "claude-tray"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / "claude-tray"
DATA_DIR = Path.home() / ".local" / "share" / "claude-tray"
SESSIONS_DIR = Path.home() / ".claude" / "sessions"
ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    # Segundos que la notificacion espera antes de devolver la pregunta a la terminal.
    # Debe ser menor que el timeout del hook (600 s).
    "approval_timeout": 540,
    # Aviso breve cuando una sesion termina o queda esperando un mensaje.
    "notify_done": True,
    # "corner": arriba a la derecha | "bubble": burbuja sobre el icono de la bandeja.
    "toast_position": "corner",
    # Mascota: nombre, color, accesorio (emoji) e icono de la bandeja ("pet" | "glyph").
    "pet": {"name": "Clawd", "color": "#D97757", "accessory": "", "tray": "pet"},
    # Silencio: 0 = avisos activos, -1 = indefinido, o epoch hasta cuando.
    "muted_until": 0,
    # Comando de status line previo, para encadenarlo.
    "statusline_chain": None,
}


def load():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text()))
    except (OSError, ValueError):
        pass
    return cfg


def save(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")
