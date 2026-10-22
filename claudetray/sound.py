"""Sonidos de aviso con el reproductor que haya en el sistema (PipeWire, PulseAudio o ALSA)."""
import shutil
import subprocess
from pathlib import Path

SOUNDS = Path(__file__).resolve().parent / "sounds"
KINDS = ("permission", "question", "done", "fail")


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


def play(kind, volume=70):
    path = SOUNDS / f"{kind}.wav"
    cmd = _player(volume)
    if cmd is None or not path.exists() or volume <= 0:
        return False
    try:
        subprocess.Popen(cmd + [str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True
