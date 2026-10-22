from traychi import hotkeys
from traychi.hotkeys import GlobalHotkeys, parse


def test_lee_atajos():
    assert parse("Super+Shift+A") == (64 | 1, "a")
    assert parse("ctrl + alt + F5") == (4 | 8, "F5")
    assert parse("Shift+Hyper+A") is None          # modificador desconocido
    assert parse("") is None


def test_en_wayland_no_intenta_capturar(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    hk = GlobalHotkeys({"allow": "Super+Shift+A"}, lambda a: None)
    assert hk.start() is False
    assert hk.failed == {"allow": "Wayland"} and hk.active == {}


def test_detecta_x11(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert hotkeys.is_x11()
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert not hotkeys.is_x11()
