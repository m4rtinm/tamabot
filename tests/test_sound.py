import wave

from claudetray import sound


def test_todos_los_sonidos_existen_y_son_wav_validos():
    for key, _label in sound.LIBRARY:
        with wave.open(str(sound.SOUNDS / f"{key}.wav")) as w:
            assert w.getnchannels() == 1 and w.getframerate() == 44100
            assert 0.15 < w.getnframes() / w.getframerate() < 1.5
    assert set(sound.DEFAULTS.values()) <= sound.NAMES


def test_elecciones_y_formato_antiguo():
    assert sound.normalize(None) == sound.DEFAULTS
    # antes eran interruptores: True = sonido por defecto, False = sin sonido
    assert sound.normalize({"permission": False, "done": True}) == {**sound.DEFAULTS, "permission": ""}
    assert sound.normalize({"question": "gota", "fail": "no-existe", "otro": "gota"}) == {**sound.DEFAULTS, "question": "gota"}


def test_elige_el_reproductor_disponible(monkeypatch):
    have = {"paplay"}
    monkeypatch.setattr(sound.shutil, "which", lambda name: f"/usr/bin/{name}" if name in have else None)
    assert sound._player(50) == ["paplay", "--volume=32768"]
    have = {"pw-play", "paplay"}
    assert sound._player(50) == ["pw-play", "--volume=0.50"]


def test_sin_reproductor_o_sin_sonido_no_falla(monkeypatch):
    assert sound.play("", 70) is False
    monkeypatch.setattr(sound.shutil, "which", lambda name: None)
    assert not sound.available()
    assert sound.play("listo") is False
