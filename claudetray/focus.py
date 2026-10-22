"""Lleva al frente la terminal (y la pestana de Konsole) donde corre una sesion."""
import shutil
import subprocess

QDBUS = shutil.which("qdbus")
WMCTRL = shutil.which("wmctrl")


def _run(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def ancestors(pid):
    chain = []
    while pid > 1 and len(chain) < 32:
        chain.append(pid)
        try:
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return chain


def _comm(pid):
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except OSError:
        return ""


def _windows_of(pid):
    if not WMCTRL:
        return []
    wins = []
    for line in _run(WMCTRL, "-lp").splitlines():
        parts = line.split(None, 4)
        if len(parts) >= 3 and parts[2] == str(pid):
            wins.append((parts[0], parts[4] if len(parts) > 4 else ""))
    return wins


def _activate(wid):
    _run(WMCTRL, "-i", "-a", wid)


def _konsole_session(kpid, chain):
    """(servicio DBus, numero de sesion) de la pestaña de Konsole cuyo proceso es ancestro de la sesion."""
    svc = f"org.kde.konsole-{kpid}"
    for path in _run(QDBUS, svc).splitlines():
        if path.startswith("/Sessions/"):
            try:
                if int(_run(QDBUS, svc, path, "processId") or 0) in chain:
                    return svc, path.rsplit("/", 1)[1]
            except ValueError:
                pass
    return None


def _find_konsole(pid):
    chain = ancestors(pid)
    for p in chain:
        if _comm(p) == "konsole" and QDBUS:
            found = _konsole_session(p, chain)
            if found:
                return p, found[0], found[1]
    return None


def _konsole(kpid, chain):
    found = _konsole_session(kpid, chain)
    if found is None:
        return False
    svc, target = found
    for path in _run(QDBUS, svc).splitlines():
        if path.startswith("/Windows/") and target in _run(QDBUS, svc, path, "sessionList").split():
            _run(QDBUS, svc, path, "setCurrentSession", target)
            break
    wins = _windows_of(kpid)
    if wins:
        title = _run(QDBUS, svc, f"/Sessions/{target}", "title", "1")
        match = next((w for w, t in wins if title and title in t), wins[0][0])
        _activate(match)
    return True


def can_send(pid):
    return bool(pid) and _find_konsole(pid) is not None


def send_text(pid, text):
    """Escribe `text` en la pestaña de Konsole de la sesion, como si lo tipearas (sin Enter)."""
    text = " ".join((text or "").split())          # una sola linea: un salto de linea lo enviaria a medias
    found = _find_konsole(pid) if text and pid else None
    if found is None:
        return False
    _, svc, target = found
    r = subprocess.run([QDBUS, svc, f"/Sessions/{target}", "sendText", text], capture_output=True, timeout=2)
    return r.returncode == 0


def send_enter(pid):
    found = _find_konsole(pid) if pid else None
    if found is None:
        return False
    _, svc, target = found
    r = subprocess.run([QDBUS, svc, f"/Sessions/{target}", "sendText", "\r"], capture_output=True, timeout=2)
    return r.returncode == 0


def focus(pid):
    if not pid:
        return False
    chain = ancestors(pid)
    for p in chain:
        if _comm(p) == "konsole" and QDBUS and _konsole(p, chain):
            return True
    for p in chain[1:]:
        wins = _windows_of(p)
        if wins:
            _activate(wins[0][0])
            return True
    return False
