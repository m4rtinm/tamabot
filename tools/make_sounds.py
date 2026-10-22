"""Genera los sonidos de la app (claudetray/sounds/*.wav): tonos suaves con desvanecimiento.

Se generan en vez de usar los del sistema para que suenen igual en cualquier distro.
"""
import math
import struct
import wave
from pathlib import Path

RATE = 44100
OUT = Path(__file__).resolve().parent.parent / "claudetray" / "sounds"

# nombre: [(frecuencia Hz, inicio s, duracion s, volumen)]
SOUNDS = {
    "permission": [(659.25, 0.00, 0.35, 0.55), (880.00, 0.11, 0.45, 0.50)],                  # mi-la, sube: "atención"
    "question": [(880.00, 0.00, 0.30, 0.45), (1108.73, 0.09, 0.30, 0.40), (1318.51, 0.18, 0.45, 0.38)],
    "done": [(1046.50, 0.00, 0.40, 0.45), (783.99, 0.13, 0.60, 0.45)],                         # do-sol, baja: "listo"
    "fail": [(440.00, 0.00, 0.30, 0.45), (349.23, 0.14, 0.45, 0.45)],
}


def render(notes):
    length = max(start + dur for _, start, dur, _ in notes) + 0.05
    samples = [0.0] * int(RATE * length)
    for freq, start, dur, vol in notes:
        s0 = int(start * RATE)
        for i in range(int(dur * RATE)):
            t = i / RATE
            attack = min(1.0, t / 0.008)                    # entrada rapida sin chasquido
            env = attack * math.exp(-t * 6.5)               # campana que se apaga
            tone = math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(4 * math.pi * freq * t)
            samples[s0 + i] += vol * env * tone * 0.8
    peak = max(1e-9, max(abs(x) for x in samples))
    gain = min(1.0, 0.9 / peak)
    return b"".join(struct.pack("<h", int(max(-1, min(1, x * gain)) * 32767)) for x in samples)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, notes in SOUNDS.items():
        with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(render(notes))
        print(name, (OUT / f"{name}.wav").stat().st_size // 1024, "KB")
