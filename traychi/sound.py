"""Sonidos de aviso con el reproductor que haya en el sistema (PipeWire, PulseAudio o ALSA)."""
import shutil
import subprocess
from pathlib import Path

SOUNDS = Path(__file__).resolve().parent / "sounds"
# sonidos disponibles, en el orden en que se recorren en Ajustes
LIBRARY = [("campana", "Campana"), ("pregunta", "Pregunta"), ("listo", "Listo"), ("error", "Error"),
           ("gota", "Gota"), ("burbuja", "Burbuja"), ("suave", "Suave"), ("triple", "Triple")]
# tipo de aviso -> sonido por defecto ("" = sin sonido)
DEFAULTS = {"permission": "campana", "question": "pregunta", "done": "listo", "fail": "error"}
KINDS = tuple(DEFAULTS)
NAMES = {key for key, _ in LIBRARY}


def _player(volume):
    """Comando para reproducir un .wav con el volumen pedido (0-100)."""
    v = max(0, min(100, int(volume))) / 100
    if shutil.which("pw-play"):
        return ["pw-play", f"--volume={v:.2f}"]
    if shutil.which("paplay"):
        return ["paplay", f"--volume={int(v * 65536)}"]
    if shutil.which("aplay"):
        return ["aplay", "-q"]                     # sin control de volumen
    return None


def available():
    return _player(100) is not None


def normalize(choices):
    """Sonido elegido por tipo de aviso. Acepta el formato antiguo (True/False)."""
    out = dict(DEFAULTS)
    for kind, value in (choices or {}).items():
        if kind not in DEFAULTS:
            continue
        if value is True:
            out[kind] = DEFAULTS[kind]
        elif value is False or value == "":
            out[kind] = ""
        elif value in NAMES:
            out[kind] = value
    return out


def play(name, volume=70):
    path = SOUNDS / f"{name}.wav"
    cmd = _player(volume)
    if not name or cmd is None or not path.exists() or volume <= 0:
        return False
    try:
        subprocess.Popen(cmd + [str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True
