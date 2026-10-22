"""Estado de sesiones y consumo, alimentado por hooks, status line y ~/.claude/sessions."""
import json
import os
import time

from .config import CACHE_DIR, SESSIONS_DIR
from .describe import activity

LONG_TASK = 10 * 60         # una tarea de mas de 10 min se celebra con confeti
HOOK_ONLY_TTL = 30 * 60     # sesiones sin archivo de pid se olvidan tras 30 min sin eventos
STALE_AFTER = 60            # ...y pasan a reposo tras 1 min sin eventos
STATE_ORDER = {"waiting": 0, "working": 1, "done": 2, "idle": 3}


def now_ms():
    return int(time.time() * 1000)


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class SessionTracker:
    def __init__(self):
        self.s = {}            # session_id -> dict
        self.ended = set()     # ids cerrados por SessionEnd (ignorar su archivo residual)

    def _get(self, sid, cwd=None):
        sess = self.s.get(sid)
        if sess is None:
            sess = self.s[sid] = {
                "sid": sid, "pid": 0, "cwd": cwd or "", "project": "", "title": "",
                "state": "idle", "activity": "", "prompt": "", "message": "",
                "modelName": "", "ctx": -1, "cost": 0.0, "updated": now_ms(),
                "pending": 0, "fromFile": False, "lastEvent": 0, "promptAt": 0,
            }
        if cwd and not sess["cwd"]:
            sess["cwd"] = cwd
        sess["project"] = os.path.basename(sess["cwd"].rstrip("/")) or sess["cwd"] or "sesión"
        return sess

    # --- fuentes -------------------------------------------------------
    def on_event(self, data):
        """Procesa un hook. Devuelve un aviso informativo opcional (dict) para mostrar."""
        sid = data.get("session_id")
        if not sid:
            return None
        ev = data.get("hook_event_name", "")
        if ev == "SessionEnd":
            self.s.pop(sid, None)
            self.ended.add(sid)
            return None
        self.ended.discard(sid)
        sess = self._get(sid, data.get("cwd"))
        sess["updated"] = sess["lastEvent"] = now_ms()
        if data.get("session_title"):
            sess["title"] = data["session_title"]
        if data.get("model") and isinstance(data["model"], str):
            sess["modelName"] = data["model"]
        notice = None
        tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}

        if ev == "SessionStart":
            sess["state"], sess["activity"] = "idle", "Sesión iniciada"
        elif ev == "UserPromptSubmit":
            sess["state"], sess["activity"] = "working", "Pensando…"
            sess["prompt"] = (data.get("prompt") or "").strip()
            sess["message"] = ""
            sess["promptAt"] = now_ms()
        elif ev == "PreToolUse":
            if tool == "AskUserQuestion":
                sess["state"] = "waiting"
            elif sess["state"] != "waiting":
                sess["state"] = "working"
            sess["activity"] = activity(tool, inp, sess["cwd"])
        elif ev == "PostToolUse":
            pass  # los hooks son asincronos: no cambiar el estado por un evento tardio
        elif ev == "PermissionRequest":
            sess["state"] = "waiting"
            sess["activity"] = "Necesita permiso · " + activity(tool, inp, sess["cwd"])
        elif ev == "Notification":
            ntype = data.get("notification_type", "")
            if ntype == "idle_prompt":
                if sess["state"] != "done":
                    sess["state"], sess["activity"] = "idle", "Esperando tu mensaje"
            elif ntype == "elicitation_dialog":
                sess["state"], sess["activity"] = "waiting", data.get("message") or "Tiene una pregunta para ti"
                notice = {"kind": "ask", "title": f"{sess['project']} te pregunta algo", "body": sess["activity"]}
            elif ntype == "permission_prompt" and sess["pending"] == 0:
                # Hay un dialogo en la terminal que no pasa por la app (p. ej. una pregunta).
                sess["state"], sess["activity"] = "waiting", data.get("message") or "Necesita tu atención"
        elif ev == "Stop":
            sess["state"], sess["activity"] = "done", "Terminado"
            msg = (data.get("last_assistant_message") or "").strip()
            sess["message"] = msg
            took = (now_ms() - sess["promptAt"]) / 1000 if sess["promptAt"] else 0
            notice = {"kind": "done", "title": f"{sess['project']} terminó", "body": msg,
                      "long": took >= LONG_TASK}
            sess["promptAt"] = 0
        elif ev == "StopFailure":
            sess["state"], sess["activity"] = "idle", "Se detuvo por un error"
            sess["promptAt"] = 0
            notice = {"kind": "fail", "title": f"{sess['project']} se detuvo por un error",
                      "body": data.get("error") or data.get("message") or ""}
        if notice:
            notice["sid"] = sid
        return notice

    def on_status(self, data):
        sid = data.get("session_id")
        if not sid or sid in self.ended:
            return
        sess = self._get(sid, (data.get("workspace") or {}).get("current_dir") or data.get("cwd"))
        model = data.get("model") or {}
        if model.get("display_name"):
            sess["modelName"] = model["display_name"]
        ctx = (data.get("context_window") or {}).get("used_percentage")
        if ctx is not None:
            sess["ctx"] = int(round(ctx))
        cost = (data.get("cost") or {}).get("total_cost_usd")
        if cost is not None:
            sess["cost"] = float(cost)
        if data.get("session_name"):
            sess["title"] = data["session_name"]

    def scan_files(self):
        """Lee ~/.claude/sessions/<pid>.json para descubrir sesiones vivas y su pid."""
        seen, present = set(), set()
        try:
            files = list(SESSIONS_DIR.glob("*.json"))
        except OSError:
            files = []
        for f in files:
            try:
                info = json.loads(f.read_text())
            except (OSError, ValueError):
                continue
            sid, pid = info.get("sessionId"), int(info.get("pid") or 0)
            if sid and pid and pid_alive(pid):
                present.add(sid)
            if not sid or sid in self.ended or not pid or not pid_alive(pid):
                continue
            seen.add(sid)
            sess = self._get(sid, info.get("cwd"))
            sess["pid"], sess["fromFile"] = pid, True
            if info.get("nameSource") not in (None, "derived") and info.get("name") and not sess["title"]:
                sess["title"] = info["name"]
            # Sin hooks recientes, el archivo es la mejor pista del estado.
            status = info.get("status")
            upd = int(info.get("statusUpdatedAt") or 0)
            if upd > sess["lastEvent"] and sess["pending"] == 0:
                if status == "busy" and sess["state"] not in ("working", "waiting"):
                    sess["state"], sess["activity"] = "working", sess["activity"] or "Trabajando…"
                elif status != "busy" and sess["state"] == "working":
                    sess["state"] = "idle"
                sess["updated"] = max(sess["updated"], upd)
        # Limpieza
        t = now_ms()
        for sid in list(self.s):
            sess = self.s[sid]
            if sess["fromFile"] and sid not in seen:
                del self.s[sid]
            elif not sess["fromFile"] and t - sess["lastEvent"] > HOOK_ONLY_TTL * 1000 and sess["pending"] == 0:
                del self.s[sid]
            elif (not sess["fromFile"] and sess["pending"] == 0 and sess["state"] in ("working", "waiting")
                  and t - sess["lastEvent"] > STALE_AFTER * 1000):
                # Sin terminal conocida y sin eventos: no seguir mostrandola como activa.
                sess["state"], sess["activity"] = "idle", "Sin actividad"
        self.ended &= present

    def set_pending(self, counts):
        for sid, sess in self.s.items():
            n = counts.get(sid, 0)
            if sess["pending"] and not n and sess["state"] == "waiting":
                sess["state"], sess["activity"] = "working", "Continuando…"
                sess["lastEvent"] = now_ms()
            sess["pending"] = n
            if n:
                sess["state"] = "waiting"

    def listing(self):
        rows = sorted(self.s.values(), key=lambda x: (STATE_ORDER.get(x["state"], 9), -x["updated"]))
        return [{k: v for k, v in r.items() if k not in ("fromFile", "lastEvent", "promptAt")} for r in rows]


class Usage:
    """Ultimo rate_limits visto (5 h / 7 d), persistido entre reinicios."""

    FILE = CACHE_DIR / "usage.json"

    def __init__(self):
        self.data = {}
        try:
            self.data = json.loads(self.FILE.read_text())
        except (OSError, ValueError):
            pass

    def on_status(self, status):
        rl = status.get("rate_limits")
        if not rl:
            return False
        new = dict(self.data)
        for key in ("five_hour", "seven_day"):
            w = rl.get(key)
            if w and w.get("used_percentage") is not None:
                new[key] = {"pct": float(w["used_percentage"]), "resets": int(w.get("resets_at") or 0)}
        new["updated"] = int(time.time())
        changed = {k: v for k, v in new.items() if k != "updated"} != {k: v for k, v in self.data.items() if k != "updated"}
        self.data = new
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self.FILE.write_text(json.dumps(self.data))
        except OSError:
            pass
        return changed

    def view(self):
        t = time.time()
        out = {"available": bool(self.data.get("five_hour") or self.data.get("seven_day")),
               "updated": self.data.get("updated", 0)}
        for key in ("five_hour", "seven_day"):
            w = self.data.get(key)
            if not w:
                out[key] = {"pct": -1, "resets": 0}
            elif w["resets"] and w["resets"] < t:
                out[key] = {"pct": 0, "resets": 0}      # la ventana ya se reinicio
            else:
                out[key] = dict(w)
        return out
