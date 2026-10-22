"""Protecciones de seguridad: carpeta del socket, permisos y entradas malformadas."""
import importlib.util
import os
from pathlib import Path

import pytest

from traychi import config
from traychi.describe import activity, describe

HOOK = Path(__file__).resolve().parent.parent / "hook" / "traychi_hook.py"


def load_hook():
    spec = importlib.util.spec_from_file_location("traychi_hook_test", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook(monkeypatch):
    mod = load_hook()
    monkeypatch.setattr(mod, "_XDG", None)     # simula un sistema sin XDG_RUNTIME_DIR (socket en /tmp)
    return mod


def test_hook_acepta_carpeta_propia_y_privada(hook, tmp_path):
    d = tmp_path / "rt"
    d.mkdir(mode=0o700)
    hook.RUNTIME = str(d)
    assert hook.runtime_is_safe()


def test_hook_rechaza_carpeta_con_permisos_abiertos(hook, tmp_path):
    d = tmp_path / "rt"
    d.mkdir()
    os.chmod(d, 0o755)
    hook.RUNTIME = str(d)
    assert not hook.runtime_is_safe()


def test_hook_rechaza_enlace_simbolico(hook, tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(real)
    hook.RUNTIME = str(link)
    assert not hook.runtime_is_safe()


def test_hook_sin_carpeta_no_se_conecta(hook, tmp_path):
    hook.RUNTIME = str(tmp_path / "no-existe")
    assert not hook.runtime_is_safe()


def test_app_rechaza_carpeta_insegura(tmp_path, monkeypatch):
    d = tmp_path / "rt"
    d.mkdir()
    os.chmod(d, 0o777)
    monkeypatch.setattr(config, "RUNTIME", d)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(d))
    with pytest.raises(RuntimeError):
        config.secure_runtime()
    os.chmod(d, 0o700)
    config.secure_runtime()                    # privada y propia: ok


def test_carpetas_de_datos_quedan_privadas(tmp_path, monkeypatch):
    for name in ("CONFIG_DIR", "CACHE_DIR", "DATA_DIR"):
        monkeypatch.setattr(config, name, tmp_path / name)
    (tmp_path / "DATA_DIR").mkdir()
    f = tmp_path / "DATA_DIR" / "history.jsonl"
    f.write_text("{}\n")
    os.chmod(f, 0o644)
    config.private_dirs()
    assert (tmp_path / "DATA_DIR").stat().st_mode & 0o777 == 0o700
    assert f.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("bad", [None, "rm -rf /", 42, ["a"], {"command": None}])
def test_entradas_malformadas_no_rompen(bad):
    d = describe("Bash", bad)
    assert set(d) >= {"title", "body", "danger"}
    assert isinstance(activity("Bash", bad), str)
    describe(None, bad)
