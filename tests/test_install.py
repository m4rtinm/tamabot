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
    subprocess.run([sys.executable, str(ROOT / "install.py"), *args], check=True, capture_output=True,
                   env={**os.environ, "HOME": str(home)})


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
        assert sum("ctray_hook.py" in c for c in cmds[ev]) == 1
    # PreToolUse: uno asincrono para todo + uno sincrono para las preguntas
    assert sum("ctray_hook.py" in c for c in cmds["PreToolUse"]) == 2
    ask = [g for g in data["hooks"]["PreToolUse"] if g.get("matcher") == "AskUserQuestion"]
    assert ask and ask[0]["hooks"][0]["command"].endswith("--ask") and not ask[0]["hooks"][0].get("async")
    assert "ctray_statusline.py" in data["statusLine"]["command"]
    cfg = json.loads((tmp_path / ".config" / "claude-tray" / "config.json").read_text())
    assert cfg["statusline_chain"] == "/x/mi_status.sh"
    assert (tmp_path / ".local" / "bin" / "claude-tray").exists()
    assert len(list(settings.parent.glob("settings.json.bak-claude-tray-*"))) == 2

    run(tmp_path, "--uninstall")
    restored = json.loads(settings.read_text())
    assert restored["hooks"] == ORIGINAL["hooks"] and restored["model"] == "opus"
    assert restored["statusLine"]["command"] == "/x/mi_status.sh"
    assert not (tmp_path / ".local" / "bin" / "claude-tray").exists()
