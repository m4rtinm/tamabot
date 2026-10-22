import wave

from claudetray import sound


def test_los_sonidos_existen_y_son_wav_validos():
    for kind in sound.KINDS:
        with wave.open(str(sound.SOUNDS / f"{kind}.wav")) as w:
            assert w.getnchannels() == 1 and w.getframerate() == 44100
            assert 0.3 < w.getnframes() / w.getframerate() < 1.5


def test_elige_el_reproductor_disponible(monkeypatch):
    have = {"paplay"}
    monkeypatch.setattr(sound.shutil, "which", lambda name: f"/usr/bin/{name}" if name in have else None)
    assert sound._player(50) == ["paplay", "--volume=32768"]
    have = {"pw-play", "paplay"}
    assert sound._player(50) == ["pw-play", "--volume=0.50"]


def test_sin_reproductor_no_falla(monkeypatch):
    monkeypatch.setattr(sound.shutil, "which", lambda name: None)
    assert not sound.available()
    assert sound.play("done") is False
