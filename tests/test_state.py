import json
import os
import time

import pytest

from traychi import state
from traychi.state import SessionTracker, Usage, now_ms


@pytest.fixture
def tracker(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "SESSIONS_DIR", tmp_path / "sessions")
    (tmp_path / "sessions").mkdir()
    return SessionTracker()


def ev(name, sid="s1", **kw):
    return {"session_id": sid, "hook_event_name": name, "cwd": "/home/u/webapp", **kw}


def test_ciclo_de_una_tarea(tracker):
    tracker.on_event(ev("UserPromptSubmit", prompt="Arregla los tests"))
    s = tracker.s["s1"]
    assert (s["state"], s["project"], s["prompt"]) == ("working", "webapp", "Arregla los tests")
    tracker.on_event(ev("PreToolUse", tool_name="Bash", tool_input={"command": "npm test"}))
    assert s["activity"] == "$ npm test"
    tracker.on_event(ev("PermissionRequest", tool_name="Bash", tool_input={"command": "git push"}))
    assert s["state"] == "waiting"
    notice = tracker.on_event(ev("Stop", last_assistant_message="Listo"))
    assert s["state"] == "done" and s["message"] == "Listo"
    assert notice["kind"] == "done" and "webapp" in notice["title"]


def test_post_tool_use_tardio_no_revive_la_sesion(tracker):
    tracker.on_event(ev("Stop"))
    tracker.on_event(ev("PostToolUse", tool_name="Bash"))
    assert tracker.s["s1"]["state"] == "done"


def test_pendientes_y_continuacion(tracker):
    tracker.on_event(ev("PermissionRequest", tool_name="Bash"))
    tracker.set_pending({"s1": 1})
    assert tracker.s["s1"]["pending"] == 1
    tracker.set_pending({})
    assert (tracker.s["s1"]["state"], tracker.s["s1"]["activity"]) == ("working", "Continuando…")


def test_session_end_la_quita_e_ignora_status_tardio(tracker):
    tracker.on_event(ev("UserPromptSubmit"))
    tracker.on_event(ev("SessionEnd"))
    assert "s1" not in tracker.s
    tracker.on_status({"session_id": "s1"})
    assert "s1" not in tracker.s


def test_sesion_sin_terminal_pasa_a_reposo_y_luego_se_olvida(tracker):
    tracker.on_event(ev("UserPromptSubmit"))
    tracker.s["s1"]["lastEvent"] = now_ms() - 2 * 60_000
    tracker.scan_files()
    assert (tracker.s["s1"]["state"], tracker.s["s1"]["activity"]) == ("idle", "Sin actividad")
    tracker.s["s1"]["lastEvent"] = now_ms() - (state.HOOK_ONLY_TTL + 60) * 1000
    tracker.scan_files()
    assert "s1" not in tracker.s


def test_descubre_sesiones_vivas_desde_archivos(tracker):
    d = state.SESSIONS_DIR
    (d / "1.json").write_text(json.dumps({"pid": os.getpid(), "sessionId": "viva", "cwd": "/x/api",
                                          "status": "busy", "statusUpdatedAt": now_ms()}))
    (d / "2.json").write_text(json.dumps({"pid": 999_999_9, "sessionId": "muerta", "cwd": "/x/old"}))
    (d / "3.json").write_text("{roto")
    tracker.scan_files()
    assert set(tracker.s) == {"viva"}
    assert tracker.s["viva"]["pid"] == os.getpid()
    assert tracker.s["viva"]["state"] == "working"
    (d / "1.json").unlink()
    tracker.scan_files()
    assert tracker.s == {}


def test_orden_esperando_primero(tracker):
    tracker.on_event(ev("Stop", sid="a"))
    tracker.on_event(ev("UserPromptSubmit", sid="b"))
    tracker.on_event(ev("PermissionRequest", sid="c", tool_name="Bash"))
    assert [r["sid"] for r in tracker.listing()] == ["c", "b", "a"]


def test_status_line_completa_datos(tracker):
    tracker.on_status({"session_id": "s1", "workspace": {"current_dir": "/p/api"}, "model": {"display_name": "Opus 5.5"},
                       "context_window": {"used_percentage": 33.6}, "cost": {"total_cost_usd": 1.5},
                       "session_name": "Arreglo de pagos"})
    s = tracker.s["s1"]
    assert (s["project"], s["modelName"], s["ctx"], s["cost"], s["title"]) == ("api", "Opus 5.5", 34, 1.5, "Arreglo de pagos")


def test_usage(tmp_path, monkeypatch):
    monkeypatch.setattr(Usage, "FILE", tmp_path / "usage.json")
    u = Usage()
    assert u.view()["available"] is False and u.view()["five_hour"]["pct"] == -1
    t = int(time.time())
    u.on_status({"rate_limits": {"five_hour": {"used_percentage": 40, "resets_at": t + 3600},
                                 "seven_day": {"used_percentage": 70, "resets_at": t - 10}}})
    v = u.view()
    assert v["five_hour"] == {"pct": 40.0, "resets": t + 3600}
    assert v["seven_day"] == {"pct": 0, "resets": 0}       # ventana ya reiniciada
    assert Usage().view()["five_hour"]["pct"] == 40.0       # persistido


def test_tarea_larga_y_fallo(tracker):
    tracker.on_event(ev("UserPromptSubmit"))
    tracker.s["s1"]["promptAt"] = now_ms() - 11 * 60_000
    assert tracker.on_event(ev("Stop"))["long"] is True
    tracker.on_event(ev("UserPromptSubmit"))
    assert tracker.on_event(ev("Stop"))["long"] is False
    notice = tracker.on_event(ev("StopFailure", error="rate_limit"))
    assert notice["kind"] == "fail" and tracker.s["s1"]["activity"] == "Se detuvo por un error"


def test_pregunta_deja_la_sesion_esperando(tracker):
    tracker.on_event(ev("UserPromptSubmit"))
    tracker.on_event(ev("PreToolUse", tool_name="AskUserQuestion",
                        tool_input={"questions": [{"question": "¿Seguimos?"}]}))
    assert tracker.s["s1"]["state"] == "waiting"
    assert tracker.s["s1"]["activity"] == "Te pregunta: ¿Seguimos?"
