#!/usr/bin/env python3
"""Instalador de Tamabot para cualquier distribución Linux.

    python3 install.py                 instala o actualiza
    python3 install.py --uninstall     desinstala (conserva tus datos)
    python3 install.py --uninstall --purge   desinstala y borra historial, mascota y config

Opciones: --no-autostart  --no-start  --no-hooks  --yes (no preguntar)
Solo usa la biblioteca estándar de Python 3.8+.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
HOME = Path.home()
SHARE = HOME / ".local" / "share" / "tamabot"
APP = SHARE / "app"                       # copia instalada del código
VENV = SHARE / "venv"                     # Python con PySide6 para la app
SETTINGS = HOME / ".claude" / "settings.json"
CONFIG_DIR = HOME / ".config" / "tamabot"
CONFIG = CONFIG_DIR / "config.json"
CACHE_DIR = HOME / ".cache" / "tamabot"
BIN = HOME / ".local" / "bin" / "tamabot"
DESKTOP = HOME / ".local" / "share" / "applications" / "tamabot.desktop"
AUTOSTART = HOME / ".config" / "autostart" / "tamabot.desktop"
ICON = HOME / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "tamabot.png"

PYSIDE = "PySide6-Essentials>=6.8,<7"
MIN_PY = (3, 12)                          # PySide6 6.12 falla en Python < 3.12 (bug de refcount de None)
MARKS = ("tamabot_", "ctray_")            # nuestras entradas en settings.json (ctray_ = Claude Tray, el nombre anterior)
LEGACY_SHARE = HOME / ".local" / "share" / "claude-tray"
LEGACY_FILES = [HOME / ".local" / "bin" / "claude-tray",
                HOME / ".local" / "share" / "applications" / "claude-tray.desktop",
                HOME / ".config" / "autostart" / "claude-tray.desktop",
                HOME / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "claude-tray.png"]
ASYNC_EVENTS = ["SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse",
                "PostToolUse", "Notification", "Stop", "StopFailure"]
COPY = ["tamabot", "hook", "VERSION", "LICENSE", "README.md"]

# libreria -> paquete por familia de distro (apt, dnf, pacman, zypper)
QT_LIBS = {
    "libxcb-cursor.so.0": ("libxcb-cursor0", "xcb-util-cursor", "xcb-util-cursor", "libxcb-cursor0"),
    "libxkbcommon-x11.so.0": ("libxkbcommon-x11-0", "libxkbcommon-x11", "libxkbcommon-x11", "libxkbcommon-x11-0"),
    "libxcb-icccm.so.4": ("libxcb-icccm4", "xcb-util-wm", "xcb-util-wm", "libxcb-icccm4"),
    "libxcb-keysyms.so.1": ("libxcb-keysyms1", "xcb-util-keysyms", "xcb-util-keysyms", "libxcb-keysyms1"),
    "libxcb-image.so.0": ("libxcb-image0", "xcb-util-image", "xcb-util-image", "libxcb-image0"),
    "libxcb-render-util.so.0": ("libxcb-render-util0", "xcb-util-renderutil", "xcb-util-renderutil", "libxcb-render-util0"),
    "libEGL.so.1": ("libegl1", "libglvnd-egl", "libglvnd", "libEGL1"),
    "libGL.so.1": ("libgl1", "libglvnd-glx", "libglvnd", "libGL1"),
    "libxkbcommon.so.0": ("libxkbcommon0", "libxkbcommon", "libxkbcommon", "libxkbcommon0"),
    "libglib-2.0.so.0": ("libglib2.0-0", "glib2", "glib2", "libglib-2_0-0"),
    "libdbus-1.so.3": ("libdbus-1-3", "dbus-libs", "dbus", "libdbus-1-3"),
    "libfontconfig.so.1": ("libfontconfig1", "fontconfig", "fontconfig", "fontconfig"),
}
# herramienta opcional -> (para que sirve, paquetes)
OPTIONAL = {
    "xprop": ("ubicar bien las ventanas sobre los paneles", ("x11-utils", "xprop", "xorg-xprop", "xprop")),
    "wmctrl": ("«Ir a la terminal»", ("wmctrl", "wmctrl", "wmctrl", "wmctrl")),
    "qdbus": ("saltar a la pestaña exacta y escribir en Konsole", ("qdbus-qt5", "qt5-qttools", "qt5-tools", "libqt5-qdbus")),
}
SOUND_PLAYERS = ("pw-play", "paplay", "aplay")
FAMILIES = ("apt", "dnf", "pacman", "zypper")
INSTALL_CMD = {"apt": "sudo apt install", "dnf": "sudo dnf install", "pacman": "sudo pacman -S", "zypper": "sudo zypper install"}

ASSUME_YES = "--yes" in sys.argv or not sys.stdin.isatty()


# --- utilidades -------------------------------------------------------------------
def say(msg=""):
    print(msg, flush=True)


def step(msg):
    say(f"\n» {msg}")


def warn(msg):
    say(f"  ! {msg}")


def die(msg):
    say(f"\n✗ {msg}")
    sys.exit(1)


def run(*cmd, **kw):
    return subprocess.run(list(cmd), capture_output=True, text=True, **kw)


def distro():
    """(nombre legible, familia de paquetes) a partir de /etc/os-release."""
    info = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k] = v.strip().strip('"')
    except OSError:
        pass
    ids = (info.get("ID", "") + " " + info.get("ID_LIKE", "")).lower()
    family = ("apt" if re.search(r"debian|ubuntu|mint|pop", ids) else
              "dnf" if re.search(r"fedora|rhel|centos|rocky|alma", ids) else
              "pacman" if re.search(r"arch|manjaro|endeavour", ids) else
              "zypper" if re.search(r"suse", ids) else None)
    return info.get("PRETTY_NAME", "Linux"), family


def pkg(family, names):
    return names[FAMILIES.index(family)] if family else names[0]


def have_lib(name):
    out = run("ldconfig", "-p").stdout if shutil.which("ldconfig") or Path("/sbin/ldconfig").exists() else ""
    if not out and Path("/sbin/ldconfig").exists():
        out = run("/sbin/ldconfig", "-p").stdout
    if name in out:
        return True
    return any(Path(d, name).exists() for d in ("/usr/lib", "/usr/lib64", "/usr/lib/x86_64-linux-gnu",
                                                 "/usr/lib/aarch64-linux-gnu", "/lib/x86_64-linux-gnu"))


def py_version(exe):
    r = run(exe, "-c", "import sys; print('%d.%d' % sys.version_info[:2])")
    try:
        return tuple(int(x) for x in r.stdout.strip().split("."))
    except ValueError:
        return None


# --- ajustes de Claude Code ----------------------------------------------------------
def load_settings():
    try:
        return json.loads(SETTINGS.read_text())
    except FileNotFoundError:
        return {}
    except ValueError as exc:
        die(f"{SETTINGS} tiene un error de formato ({exc}). Corrígelo antes de instalar; no se tocó nada.")


def save_settings(data):
    if SETTINGS.exists():
        stamp, n = time.strftime("%Y%m%d-%H%M%S"), 0
        backup = SETTINGS.with_name(f"settings.json.bak-tamabot-{stamp}")
        while backup.exists():
            n += 1
            backup = SETTINGS.with_name(f"settings.json.bak-tamabot-{stamp}-{n}")
        shutil.copy2(SETTINGS, backup)
        say(f"  respaldo de tus ajustes: {backup}")
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    # escritura atomica: si algo se corta, settings.json nunca queda a medias
    fd, tmp = tempfile.mkstemp(dir=SETTINGS.parent, prefix=".settings.", suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    if SETTINGS.exists():
        shutil.copymode(SETTINGS, tmp)
    os.replace(tmp, SETTINGS)


def is_ours(command):
    return any(m in (command or "") for m in MARKS)


def strip_ours(hooks):
    """Quita las entradas de Tamabot (y de Claude Tray, su nombre anterior) sin tocar las demás."""
    for event in list(hooks):
        groups = []
        for group in hooks[event]:
            kept = [h for h in group.get("hooks", []) if not is_ours(h.get("command", ""))]
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
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")
    os.chmod(CONFIG, 0o600)


def hook_commands(app_dir):
    py = shutil.which("python3") or "/usr/bin/python3"       # los hooks solo usan la stdlib
    q = shlex.quote
    hook = f"{q(py)} -I -S {q(str(app_dir / 'hook' / 'tamabot_hook.py'))}"
    status = f"{q(py)} -I -S {q(str(app_dir / 'hook' / 'tamabot_statusline.py'))}"
    return hook, status


def install_hooks(app_dir):
    step("Conectando con Claude Code (hooks y status line)")
    data = load_settings()
    hook, status = hook_commands(app_dir)
    hooks = strip_ours(data.get("hooks", {}))
    hooks.setdefault("PermissionRequest", []).append(
        {"matcher": "*", "hooks": [{"type": "command", "command": hook, "timeout": 600}]})
    # preguntas con opciones: PreToolUse sincrono solo para AskUserQuestion
    hooks.setdefault("PreToolUse", []).append(
        {"matcher": "AskUserQuestion", "hooks": [{"type": "command", "command": hook + " --ask", "timeout": 600}]})
    for ev in ASYNC_EVENTS:
        hooks.setdefault(ev, []).append({"hooks": [{"type": "command", "command": hook, "async": True, "timeout": 5}]})
    data["hooks"] = hooks
    cfg = load_config()
    current = data.get("statusLine")
    if current and not is_ours(current.get("command", "")):
        cfg["statusline_chain"] = current.get("command")
        say(f"  tu status line actual se sigue mostrando: {cfg['statusline_chain']}")
    data["statusLine"] = {"type": "command", "command": status, "padding": 0}
    save_settings(data)
    save_config(cfg)
    say("  listo. Las sesiones de Claude Code ya abiertas los toman al reiniciarse.")


def remove_hooks():
    data = load_settings()
    if not data:
        return
    if "hooks" in data:
        data["hooks"] = strip_ours(data["hooks"])
        if not data["hooks"]:
            del data["hooks"]
    if is_ours((data.get("statusLine") or {}).get("command", "")):
        chain = load_config().get("statusline_chain")
        if chain:
            data["statusLine"] = {"type": "command", "command": chain}
        else:
            del data["statusLine"]
    save_settings(data)


# --- comprobaciones del sistema ------------------------------------------------------
def check_system():
    step("Revisando el sistema")
    name, family = distro()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "desconocido")
    session = os.environ.get("XDG_SESSION_TYPE", "desconocida")
    say(f"  {name} · escritorio {desktop} · sesión {session}")
    if not sys.platform.startswith("linux"):
        die("Tamabot es para Linux.")
    if not shutil.which("claude"):
        warn("No encontré el comando «claude» (Claude Code). La app se instala igual y funcionará cuando lo instales.")

    missing = [lib for lib in QT_LIBS if not have_lib(lib)]
    if missing:
        pkgs = " ".join(sorted({pkg(family, QT_LIBS[lib]) for lib in missing}))
        warn("Faltan librerías que Qt necesita para mostrar ventanas: " + ", ".join(missing))
        say(f"    instálalas con:  {INSTALL_CMD.get(family, 'tu gestor de paquetes:')} {pkgs}")
    for tool, (why, names) in OPTIONAL.items():
        if not shutil.which(tool) and not (tool == "qdbus" and (shutil.which("qdbus-qt5") or shutil.which("qdbus6"))):
            if tool == "qdbus" and "KDE" not in desktop.upper():
                continue
            say(f"  · opcional: «{tool}» para {why}  ({INSTALL_CMD.get(family, 'instala')} {pkg(family, names)})")
    if not any(shutil.which(p) for p in SOUND_PLAYERS):
        say("  · opcional: no hay reproductor de audio (pw-play, paplay o aplay): no habrá sonidos.")
    if "GNOME" in desktop.upper():
        ext = run("gnome-extensions", "list", "--enabled").stdout if shutil.which("gnome-extensions") else ""
        if "appindicator" not in ext.lower():
            warn("GNOME no muestra iconos de bandeja sin la extensión «AppIndicator and KStatusNotifierItem Support».")
            say("    instálala desde https://extensions.gnome.org/extension/615/ (o el paquete gnome-shell-extension-appindicator).")
            say("    Sin ella la app funciona igual: abre el panel con «tamabot --panel».")
    return family


def find_python():
    """Un Python >= 3.12 del sistema, o None."""
    for exe in ("python3.14", "python3.13", "python3.12", "python3"):
        path = shutil.which(exe)
        if path and (py_version(path) or (0, 0)) >= MIN_PY:
            return path
    return None


def build_venv(family):
    step("Preparando Python con PySide6")
    if (VENV / "bin" / "python").exists():
        ok = run(str(VENV / "bin" / "python"), "-c", "import PySide6, sys; assert sys.version_info >= (3, 12)").returncode == 0
        if ok:
            say("  ya estaba listo; se actualiza PySide6 si hace falta")
            r = run(str(VENV / "bin" / "python"), "-m", "pip", "install", "-q", "--upgrade", PYSIDE)
            if r.returncode != 0 and shutil.which("uv"):
                run("uv", "pip", "install", "-q", "--python", str(VENV / "bin" / "python"), PYSIDE)
            return
        shutil.rmtree(VENV)
    py = find_python()
    if py:
        say(f"  usando {py} ({'.'.join(map(str, py_version(py)))})")
        r = run(py, "-m", "venv", str(VENV))
        if r.returncode != 0:
            if family == "apt":
                v = ".".join(map(str, py_version(py)))
                die(f"Python no puede crear entornos virtuales. Instala:  sudo apt install python{v}-venv  y vuelve a ejecutar.")
            die(f"No se pudo crear el entorno: {r.stderr.strip()}")
        say("  descargando PySide6 (unos 100 MB, solo la primera vez)…")
        r = run(str(VENV / "bin" / "python"), "-m", "pip", "install", "-q", "--upgrade", "pip", PYSIDE)
        if r.returncode != 0:
            die(f"No se pudo instalar PySide6:\n{r.stderr.strip()[-800:]}")
        return
    if shutil.which("uv"):
        say("  tu Python es anterior a 3.12: uv descarga uno aparte (no toca el del sistema)")
        r = run("uv", "venv", "-q", "--python", "3.12", str(VENV))
        if r.returncode != 0:
            die(f"uv no pudo crear el entorno: {r.stderr.strip()}")
        say("  descargando PySide6 (unos 100 MB, solo la primera vez)…")
        r = run("uv", "pip", "install", "-q", "--python", str(VENV / "bin" / "python"), PYSIDE)
        if r.returncode != 0:
            die(f"No se pudo instalar PySide6:\n{r.stderr.strip()[-800:]}")
        return
    die("Hace falta Python 3.12 o superior (tu sistema tiene uno anterior). La forma más simple:\n"
        "  instalar uv, que descarga un Python aparte sin tocar el del sistema:\n"
        "      curl -LsSf https://astral.sh/uv/install.sh | sh      (o desde https://docs.astral.sh/uv/)\n"
        f"  o, si tu distro lo ofrece:  {INSTALL_CMD.get(family, 'tu gestor de paquetes:')} python3.12"
        f"{' python3.12-venv' if family == 'apt' else ''}\n"
        "Luego vuelve a ejecutar este instalador.")


# --- archivos de la app ----------------------------------------------------------------
def check_qt(family):
    """Prueba que Qt cargue de verdad; si falta una libreria, dice cual y como instalarla."""
    r = run(str(VENV / "bin" / "python"), "-c", "import PySide6.QtGui, PySide6.QtQuick")
    if r.returncode == 0:
        say("  Qt carga correctamente")
        return True
    m = re.search(r"(lib[\w.+-]+\.so[\w.]*): cannot open shared object", r.stderr)
    lib = m.group(1) if m else None
    if lib in QT_LIBS:
        warn(f"Qt no puede cargar porque falta {lib}.  Instálala con:  {INSTALL_CMD.get(family, 'instala')} {pkg(family, QT_LIBS[lib])}")
    elif lib:
        warn(f"Qt no puede cargar porque falta {lib}. Instala el paquete que la contiene y vuelve a ejecutar el instalador.")
    else:
        warn("Qt no pudo cargar: " + r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "Qt no pudo cargar.")
    return False


def migrate_legacy():
    """Si estaba instalado como Claude Tray: mueve tus datos y quita lo antiguo."""
    old_dirs = {"config": HOME / ".config" / "claude-tray", "cache": HOME / ".cache" / "claude-tray",
                "data": LEGACY_SHARE}
    new_dirs = {"config": CONFIG_DIR, "cache": CACHE_DIR, "data": SHARE}
    found = False
    for key, old in old_dirs.items():
        if not old.is_dir():
            continue
        found = True
        new_dirs[key].mkdir(parents=True, exist_ok=True)
        for f in old.iterdir():
            if f.is_file() and not (new_dirs[key] / f.name).exists():
                f.rename(new_dirs[key] / f.name)
        for sub in ("app", "venv", "app.new"):          # la app antigua se reinstala, no se mueve
            if (old / sub).is_dir():
                shutil.rmtree(old / sub)
        if not any(old.iterdir()):
            old.rmdir()
    for f in LEGACY_FILES:
        if f.exists():
            f.unlink()
            found = True
    if found:
        step("Se encontró Claude Tray (el nombre anterior): tus datos pasaron a Tamabot")
    return found


def copy_app():
    step(f"Copiando la app a {APP}")
    new = SHARE / "app.new"
    if new.exists():
        shutil.rmtree(new)
    new.mkdir(parents=True)
    for name in COPY:
        src = SRC / name
        if src.is_dir():
            shutil.copytree(src, new / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif src.exists():
            shutil.copy2(src, new / name)
    if APP.exists():
        shutil.rmtree(APP)
    new.rename(APP)                        # se reemplaza de una vez: nunca queda una copia a medias
    os.chmod(SHARE, 0o700)


def write_launcher():
    step("Creando el lanzador, el menú y el autoarranque")
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.write_text("#!/bin/sh\n"
                   f"cd {shlex.quote(str(APP))} || exit 1\n"
                   f"exec {shlex.quote(str(VENV / 'bin' / 'python'))} -m tamabot \"$@\"\n")
    BIN.chmod(0o755)
    ICON.parent.mkdir(parents=True, exist_ok=True)
    if (VENV / "bin" / "python").exists():
        run(str(VENV / "bin" / "python"), "-c",
            "from PySide6.QtGui import QGuiApplication; app = QGuiApplication([]);"
            f"from tamabot.icon import save_png; save_png({str(ICON)!r})",
            cwd=APP, env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
    entry = ("[Desktop Entry]\nType=Application\nName=Tamabot\n"
             "Comment=Aprueba solicitudes y sigue tus sesiones de Claude Code desde la bandeja\n"
             f"Exec={BIN}\nIcon={ICON if ICON.exists() else 'utilities-terminal'}\nTerminal=false\n"
             "Categories=Development;Utility;\nStartupNotify=false\nX-KDE-autostart-after=panel\n"
             "X-GNOME-Autostart-Delay=3\n")
    DESKTOP.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP.write_text(entry)
    if "--no-autostart" not in sys.argv:
        AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
        AUTOSTART.write_text(entry)
    path_dirs = os.environ.get("PATH", "").split(":")
    if str(BIN.parent) not in path_dirs:
        warn(f"{BIN.parent} no está en tu PATH: agrega  export PATH=\"$HOME/.local/bin:$PATH\"  a tu ~/.bashrc o ~/.zshrc")


# --- atajos en GNOME/Wayland (en X11 los registra la app sola) ---------------------------
GNOME_KEYS = "org.gnome.settings-daemon.plugins.media-keys"
GNOME_BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
GNOME_SHORTCUTS = {"tamabot-allow": ("Tamabot: permitir", "--allow", "<Super><Shift>a"),
                   "tamabot-deny": ("Tamabot: rechazar", "--deny", "<Super><Shift>d"),
                   "tamabot-panel": ("Tamabot: panel", "--panel", "<Super><Shift>c")}


def _gnome_list():
    out = run("gsettings", "get", GNOME_KEYS, "custom-keybindings").stdout.strip()
    return re.findall(r"'([^']+)'", out)


def gnome_shortcuts(add=True):
    if not shutil.which("gsettings") or "GNOME" not in os.environ.get("XDG_CURRENT_DESKTOP", "").upper():
        return
    current = [p for p in _gnome_list() if "tamabot-" not in p and "claude-tray-" not in p]
    if add:
        if os.environ.get("XDG_SESSION_TYPE") != "wayland":
            return                         # en X11 la app los registra sola
        step("Registrando atajos en GNOME (Wayland)")
        for key, (name, flag, binding) in GNOME_SHORTCUTS.items():
            path = f"{GNOME_BASE}{key}/"
            schema = f"{GNOME_KEYS}.custom-keybinding:{path}"
            run("gsettings", "set", schema, "name", name)
            run("gsettings", "set", schema, "command", f"{BIN} {flag}")
            run("gsettings", "set", schema, "binding", binding)
            current.append(path)
            say(f"  {binding.replace('<', '').replace('>', '+')}  →  {name}")
    run("gsettings", "set", GNOME_KEYS, "custom-keybindings", "[" + ", ".join(f"'{p}'" for p in current) + "]")


# --- arranque / parada -------------------------------------------------------------------
def stop_running():
    """Detiene Tamabot si esta abierto (tambien una instalacion antigua, desde otra carpeta)."""
    if not shutil.which("pkill"):
        return
    r = run("pkill", "-u", str(os.getuid()), "-f", r"python[0-9.]* -m (tamabot|claudetray)( |$)")
    if r.returncode == 0:
        time.sleep(1)


def start_app():
    if "--no-start" in sys.argv or not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return
    subprocess.Popen([str(BIN)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    say("  Tamabot está abierto: busca su icono en la bandeja.")


# --- principal ------------------------------------------------------------------------------
def install():
    from_src = (SRC / "tamabot" / "app.py").exists()
    if not from_src:
        die("Ejecuta el instalador desde la carpeta del proyecto (la que tiene tamabot/ y hook/).")
    version = (SRC / "VERSION").read_text().strip() if (SRC / "VERSION").exists() else "?"
    say(f"Tamabot {version} · instalador")
    family = check_system()
    if not ASSUME_YES:
        ans = input("\n¿Continuar con la instalación? [S/n] ").strip().lower()
        if ans in ("n", "no"):
            die("Cancelado.")
    stop_running()
    migrate_legacy()
    copy_app()
    qt_ok = True
    if "--no-venv" not in sys.argv:        # --no-venv: solo para los tests
        build_venv(family)
        qt_ok = check_qt(family)
    write_launcher()
    if "--no-hooks" not in sys.argv:
        install_hooks(APP)
    gnome_shortcuts(add=True)
    if not qt_ok:
        say("\n✓ Instalación completa, pero la app no abrirá hasta instalar lo que falta (ver arriba).")
        say("  Después de instalarlo, ejecuta «tamabot» (no hace falta reinstalar).")
        return
    say("\n✓ Instalación completa.")
    say("  · Ábrelo desde el menú o con «tamabot». Se abre solo al iniciar sesión.")
    say("  · Atajos: Super+Shift+A permitir · Super+Shift+D rechazar · Super+Shift+C panel.")
    say("  · Para desinstalar:  python3 install.py --uninstall")
    start_app()


def uninstall():
    say("Desinstalando Tamabot…")
    stop_running()
    remove_hooks()
    gnome_shortcuts(add=False)
    for path in (BIN, DESKTOP, AUTOSTART, ICON):
        if path.exists():
            path.unlink()
    for d in (APP, VENV, SHARE / "app.new"):
        if d.exists():
            shutil.rmtree(d)
    if "--purge" in sys.argv:
        for d in (SHARE, CONFIG_DIR, CACHE_DIR):
            if d.exists():
                shutil.rmtree(d)
        say("  también se borraron tu historial, la mascota y la configuración.")
    else:
        say(f"  tus datos quedan en {SHARE}, {CONFIG_DIR} y {CACHE_DIR} (bórralos con --purge).")
    say("✓ Listo.")


if __name__ == "__main__":
    uninstall() if "--uninstall" in sys.argv else install()
