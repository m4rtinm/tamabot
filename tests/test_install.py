"""install.py contra un HOME temporal: conserva lo ajeno y se deshace limpio."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORIGINAL = {
    "model": "opus",
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "/x/mi_hook.sh"}]}]},
    "statusLine": {"type": "command", "command": "/x/mi_status.sh"},
}


def run(home, *args):
    # --no-venv: no descarga PySide6 en los tests; --yes y --no-start: sin preguntas ni ventanas
    subprocess.run([sys.executable, str(ROOT / "install.py"), "--yes", "--no-start", "--no-venv", *args],
                   check=True, capture_output=True, env={**os.environ, "HOME": str(home)})


def test_instalar_dos_veces_y_desinstalar(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps(ORIGINAL))

    run(tmp_path)
    run(tmp_path)                          # idempotente
    data = json.loads(settings.read_text())
    cmds = {ev: [h["command"] for g in groups for h in g["hooks"]] for ev, groups in data["hooks"].items()}
    assert "/x/mi_hook.sh" in cmds["PreToolUse"]
    for ev in ("PermissionRequest", "Stop", "SessionStart", "StopFailure"):
        assert sum("tamabot_hook.py" in c for c in cmds[ev]) == 1
    # PreToolUse: uno asincrono para todo + uno sincrono para las preguntas
    assert sum("tamabot_hook.py" in c for c in cmds["PreToolUse"]) == 2
    ask = [g for g in data["hooks"]["PreToolUse"] if g.get("matcher") == "AskUserQuestion"]
    assert ask and ask[0]["hooks"][0]["command"].endswith("--ask") and not ask[0]["hooks"][0].get("async")
    assert "tamabot_statusline.py" in data["statusLine"]["command"]
    cfg = json.loads((tmp_path / ".config" / "tamabot" / "config.json").read_text())
    assert cfg["statusline_chain"] == "/x/mi_status.sh"
    assert (tmp_path / ".local" / "bin" / "tamabot").exists()
    assert len(list(settings.parent.glob("settings.json.bak-tamabot-*"))) == 2
    # la app queda copiada fuera de la carpeta del proyecto, y los hooks apuntan ahi
    app = tmp_path / ".local" / "share" / "tamabot" / "app"
    assert (app / "tamabot" / "app.py").exists() and (app / "hook" / "tamabot_hook.py").exists()
    assert str(app / "hook" / "tamabot_hook.py") in cmds["PermissionRequest"][0]
    assert not list(app.rglob("__pycache__"))

    run(tmp_path, "--uninstall")
    restored = json.loads(settings.read_text())
    assert restored["hooks"] == ORIGINAL["hooks"] and restored["model"] == "opus"
    assert restored["statusLine"]["command"] == "/x/mi_status.sh"
    assert not (tmp_path / ".local" / "bin" / "tamabot").exists()
    assert not app.exists()
    assert (tmp_path / ".config" / "tamabot").exists()          # sin --purge, tus datos quedan


def test_settings_json_daniado_no_se_toca(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text('{"hooks": {roto')
    r = subprocess.run([sys.executable, str(ROOT / "install.py"), "--yes", "--no-start", "--no-venv"],
                       capture_output=True, text=True, env={**os.environ, "HOME": str(tmp_path)})
    assert r.returncode == 1 and "error de formato" in r.stdout
    assert settings.read_text() == '{"hooks": {roto'


def test_rutas_con_espacios_quedan_entrecomilladas(tmp_path):
    home = tmp_path / "mi carpeta"
    home.mkdir()
    run(home)
    data = json.loads((home / ".claude" / "settings.json").read_text())
    cmd = data["hooks"]["PermissionRequest"][0]["hooks"][0]["command"]
    assert "'" in cmd and "mi carpeta" in cmd                    # shlex.quote


def test_actualizar_desde_claude_tray(tmp_path):
    """Quien tenia Claude Tray (el nombre anterior) conserva sus datos y no quedan restos."""
    old_hook = "/usr/bin/python3 -I -S /x/.local/share/claude-tray/app/hook/ctray_hook.py"
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({
        "hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "/x/mi_hook.sh"}]},
                                 {"hooks": [{"type": "command", "command": old_hook, "async": True}]}],
                  "Stop": [{"hooks": [{"type": "command", "command": old_hook, "async": True}]}]},
        "statusLine": {"type": "command", "command": "/usr/bin/python3 -I -S /x/hook/ctray_statusline.py"},
    }))
    (tmp_path / ".config" / "claude-tray").mkdir(parents=True)
    (tmp_path / ".config" / "claude-tray" / "config.json").write_text('{"pet": {"name": "Clawd"}}')
    (tmp_path / ".local" / "share" / "claude-tray" / "app").mkdir(parents=True)
    (tmp_path / ".local" / "share" / "claude-tray" / "history.jsonl").write_text('{"ts": 1, "kind": "done"}\n')
    old_bin = tmp_path / ".local" / "bin" / "claude-tray"
    old_bin.parent.mkdir(parents=True)
    old_bin.write_text("#!/bin/sh\n")

    run(tmp_path)

    data = json.loads(settings.read_text())
    cmds = [h["command"] for groups in data["hooks"].values() for g in groups for h in g["hooks"]]
    assert not any("ctray_" in c for c in cmds)                       # hooks antiguos fuera
    assert "/x/mi_hook.sh" in cmds                                     # los tuyos, intactos
    assert "tamabot_statusline.py" in data["statusLine"]["command"]
    cfg = json.loads((tmp_path / ".config" / "tamabot" / "config.json").read_text())
    assert not cfg.get("statusline_chain")                            # la vieja no se encadena consigo misma
    assert (tmp_path / ".local" / "share" / "tamabot" / "history.jsonl").exists()
    assert not (tmp_path / ".local" / "share" / "claude-tray" / "app").exists()
    assert not old_bin.exists() and (tmp_path / ".local" / "bin" / "tamabot").exists()
