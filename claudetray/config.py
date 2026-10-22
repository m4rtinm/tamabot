import json
import os
import stat
from pathlib import Path


def _runtime_dir():
    base = os.environ.get("XDG_RUNTIME_DIR")
    if base and os.path.isdir(base):
        return Path(base)
    return Path(f"/tmp/claude-tray-{os.getuid()}")


RUNTIME = _runtime_dir()
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
    # Sonidos por tipo de aviso y volumen (0-100).
    "sounds": {"permission": True, "question": True, "done": True, "fail": True},
    "sound_volume": 70,
    # Atajos globales (X11 los registra la app; en Wayland se asignan los comandos en el escritorio).
    "global_shortcuts": True,
    "shortcuts": {"allow": "Super+Shift+A", "deny": "Super+Shift+D", "panel": "Super+Shift+C"},
    # Silencio: 0 = avisos activos, -1 = indefinido, o epoch hasta cuando.
    "muted_until": 0,
    # Comando de status line previo, para encadenarlo.
    "statusline_chain": None,
}


def secure_runtime():
    """Crea la carpeta del socket si hace falta y verifica que sea nuestra y privada.

    Sin XDG_RUNTIME_DIR el socket va a /tmp: otro usuario podria crear esa carpeta antes
    y recibir (y aprobar) nuestras solicitudes. Por eso se exige dueño propio y modo 0700.
    """
    path = RUNTIME
    if not os.environ.get("XDG_RUNTIME_DIR"):
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            pass
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise RuntimeError(f"La carpeta del socket {path} no es privada o no es tuya; no se usa por seguridad.")


def private_dirs():
    """Las carpetas de la app solo las lee su dueño (el historial guarda comandos)."""
    for d in (CONFIG_DIR, CACHE_DIR, DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)
        os.chmod(d, 0o700)
        for f in d.iterdir():
            if f.is_file():
                os.chmod(f, 0o600)


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
