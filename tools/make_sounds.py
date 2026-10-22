"""Genera los sonidos de la app (tamabot/sounds/*.wav): tonos suaves con desvanecimiento.

Se generan en vez de usar los del sistema para que suenen igual en cualquier distro.
"""
import math
import struct
import wave
from pathlib import Path

RATE = 44100
OUT = Path(__file__).resolve().parent.parent / "tamabot" / "sounds"

# nombre: [(frecuencia Hz, inicio s, duracion s, volumen[, frecuencia final para un barrido])]
SOUNDS = {
    "campana": [(659.25, 0.00, 0.35, 0.55), (880.00, 0.11, 0.45, 0.50)],                     # sube: "atencion"
    "pregunta": [(880.00, 0.00, 0.30, 0.45), (1108.73, 0.09, 0.30, 0.40), (1318.51, 0.18, 0.45, 0.38)],
    "listo": [(1046.50, 0.00, 0.40, 0.45), (783.99, 0.13, 0.60, 0.45)],                       # baja: "listo"
    "error": [(440.00, 0.00, 0.30, 0.45), (349.23, 0.14, 0.45, 0.45)],
    "gota": [(1400.0, 0.00, 0.18, 0.55, 620.0)],
    "burbuja": [(520.0, 0.00, 0.12, 0.50, 980.0), (700.0, 0.13, 0.12, 0.40, 1250.0)],
    "suave": [(523.25, 0.00, 0.80, 0.45)],
    "triple": [(987.77, 0.00, 0.14, 0.40), (987.77, 0.15, 0.14, 0.40), (987.77, 0.30, 0.30, 0.40)],
}


def render(notes):
    length = max(n[1] + n[2] for n in notes) + 0.05
    samples = [0.0] * int(RATE * length)
    for note in notes:
        freq, start, dur, vol = note[:4]
        end_freq = note[4] if len(note) > 4 else freq
        s0 = int(start * RATE)
        phase = 0.0
        for i in range(int(dur * RATE)):
            t = i / RATE
            f = freq + (end_freq - freq) * (t / dur)         # barrido lineal (gota, burbuja)
            phase += 2 * math.pi * f / RATE
            attack = min(1.0, t / 0.008)                    # entrada rapida sin chasquido
            env = attack * math.exp(-t * (6.5 if end_freq == freq else 14))
            tone = math.sin(phase) + 0.25 * math.sin(2 * phase)
            samples[s0 + i] += vol * env * tone * 0.8
    peak = max(1e-9, max(abs(x) for x in samples))
    gain = min(1.0, 0.9 / peak)
    return b"".join(struct.pack("<h", int(max(-1, min(1, x * gain)) * 32767)) for x in samples)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.wav"):
        old.unlink()
    for name, notes in SOUNDS.items():
        with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(render(notes))
        print(name, (OUT / f"{name}.wav").stat().st_size // 1024, "KB")
