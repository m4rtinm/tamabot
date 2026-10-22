"""El hook real (hook/traychi_hook.py) contra un servidor falso."""
import json
import os
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "hook" / "traychi_hook.py"


@pytest.fixture
def env(tmp_path):
    run = tmp_path / "r"
    run.mkdir()
    return {**os.environ, "XDG_RUNTIME_DIR": str(run), "HOME": str(tmp_path)}


def serve(env, reply=None):
    """Acepta una conexion, guarda el mensaje y responde (o no)."""
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(os.path.join(env["XDG_RUNTIME_DIR"], "traychi.sock"))
    srv.listen(1)
    got = {}

    def run():
        conn, _ = srv.accept()
        buf = b""
        while b"\n" not in buf:
            buf += conn.recv(65536)
        got["msg"] = json.loads(buf.split(b"\n")[0])
        if reply is not None:
            conn.sendall((json.dumps(reply) + "\n").encode())
            conn.close()
        else:
            got["conn"] = conn            # sin respuesta: se deja abierta

    threading.Thread(target=run, daemon=True).start()
    return got


def call(env, data, timeout=10, args=()):
    return subprocess.run(["/usr/bin/python3", "-I", "-S", str(HOOK), *args], input=json.dumps(data),
                          capture_output=True, text=True, env=env, timeout=timeout)


PERM = {"session_id": "s", "hook_event_name": "PermissionRequest", "tool_name": "Bash",
        "tool_input": {"command": "ls"}}


def test_devuelve_la_decision_en_el_formato_de_claude_code(env):
    got = serve(env, {"decision": {"behavior": "allow"}})
    out = call(env, PERM)
    assert json.loads(out.stdout) == {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                                                             "decision": {"behavior": "allow"}}}
    assert got["msg"]["kind"] == "permission" and got["msg"]["data"]["tool_name"] == "Bash"


def test_sin_app_no_imprime_nada_y_claude_pregunta_en_la_terminal(env):
    out = call(env, PERM)
    assert out.returncode == 0 and out.stdout == ""


def test_sin_decision_deja_el_flujo_normal(env):
    serve(env, {"decision": None})
    assert call(env, PERM).stdout == ""


def test_eventos_no_esperan_respuesta(env):
    got = serve(env)
    t = time.monotonic()
    out = call(env, {"session_id": "s", "hook_event_name": "Stop"})
    assert out.stdout == "" and time.monotonic() - t < 3
    time.sleep(0.1)
    assert got["msg"]["kind"] == "event"


def test_respeta_el_tiempo_de_espera_configurado(env, tmp_path):
    cfg = tmp_path / ".config" / "traychi"
    cfg.mkdir(parents=True)
    (cfg / "config.json").write_text(json.dumps({"approval_timeout": 1}))
    got = serve(env)                      # nunca responde (got mantiene viva la conexion)
    t = time.monotonic()
    out = call(env, PERM)
    waited = time.monotonic() - t
    assert out.stdout == "" and 0.9 <= waited < 4
    assert "conn" in got


ASK = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion",
       "tool_input": {"questions": [{"question": "¿Cuál?", "header": "X", "multiSelect": False,
                                     "options": [{"label": "A"}, {"label": "B"}]}]}}


def test_pregunta_respondida_desde_la_app(env):
    got = serve(env, {"answers": {"¿Cuál?": "B"}})
    out = json.loads(call(env, ASK, args=["--ask"]).stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse" and out["permissionDecision"] == "allow"
    # updatedInput reemplaza todo: deben volver las preguntas originales + las respuestas
    assert out["updatedInput"]["questions"] == ASK["tool_input"]["questions"]
    assert out["updatedInput"]["answers"] == {"¿Cuál?": "B"}
    assert got["msg"]["kind"] == "question"


def test_pregunta_sin_respuesta_vuelve_a_la_terminal(env):
    serve(env, {"decision": None})
    assert call(env, ASK, args=["--ask"]).stdout == ""


def test_modo_ask_ignora_otras_herramientas(env):
    t = time.monotonic()
    out = call(env, {**PERM, "hook_event_name": "PreToolUse"}, args=["--ask"])
    assert out.stdout == "" and time.monotonic() - t < 2
