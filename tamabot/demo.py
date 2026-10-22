"""Datos de ejemplo para revisar el diseno (python -m tamabot --demo)."""
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QTimer

from . import state
from .history import History
from .usagehist import DailyUsage
from .pet import PetState
from .state import now_ms


def load_demo(ctrl):
    t = int(time.time())
    # Historial de ejemplo en un archivo temporal: la demo nunca toca el real.
    tmp = Path(tempfile.mkdtemp(prefix="tamabot-demo-"))
    ctrl.history = History(tmp / "history.jsonl")
    ctrl.petstate = PetState(tmp / "pet-state.json", now=t - 9 * 86400)
    ctrl.petstate.d.update(hunger=42, energy=76, happy=88, xp=260, updated=t)
    # la demo no lee tus sesiones ni tu consumo reales: todo es de ejemplo
    state.SESSIONS_DIR = tmp / "sessions"
    ctrl.tracker.s.clear()
    ctrl.daily = DailyUsage(root=tmp / "projects", cache_path=tmp / "daily.json")
    pattern = [1.6, 0.4, 1.5, 0.2, 0.0, 2.3, 1.9, 1.1, 0.9, 1.7, 0.0, 0.3, 1.2, 2.0, 1.4]
    for i in range(30):
        day = (date.today() - timedelta(days=i)).isoformat()
        total = int(pattern[i % len(pattern)] * 1_000_000)
        if total:
            ctrl.daily.days[day] = {"input": total // 50, "output": total // 10, "cache_write": total - total // 50 - total // 10,
                                    "cache_read": total * 9, "messages": total // 9000}
    ctrl._daily_ready(from_worker=False)
    for ago, outcome, proj, title, detail, danger in (
            (60, "allow", "webapp", "Ejecutar comando", "npm test -- payments", False),
            (400, "deny", "api-gateway", "Ejecutar comando", "rm -rf build/ dist/", True),
            (900, "always", "webapp", "Editar archivo", "src/payments/charge.ts", False),
            (3000, "elsewhere", "landing", "Ejecutar comando", "git push origin main", False),
            (90000, "timeout", "api-gateway", "Abrir página web", "https://docs.example.com", False)):
        ctrl.history.add("decision", ts=t - ago, outcome=outcome, project=proj, title=title,
                         detail=detail, danger=danger, tool="Bash")
    for ago in (200, 86400 + 50, 2 * 86400 + 50):
        ctrl.history.add("done", ts=t - ago, project="landing")
    ctrl.historyChanged.emit()
    home = "/home/demo/proyectos"
    events = [
        {"session_id": "d1", "hook_event_name": "UserPromptSubmit", "cwd": f"{home}/webapp",
         "prompt": "Arregla los tests que fallan en el módulo de pagos"},
        {"session_id": "d1", "hook_event_name": "PreToolUse", "cwd": f"{home}/webapp",
         "tool_name": "Bash", "tool_input": {"command": "npm test -- payments --coverage"}},
        {"session_id": "d2", "hook_event_name": "UserPromptSubmit", "cwd": f"{home}/api-gateway",
         "prompt": "Revisa el rate limiter"},
        {"session_id": "d3", "hook_event_name": "UserPromptSubmit", "cwd": f"{home}/landing",
         "prompt": "Ajusta el hero para móvil"},
        {"session_id": "d3", "hook_event_name": "Stop", "cwd": f"{home}/landing",
         "last_assistant_message": "Listo: el hero ahora usa clamp() para el título y la imagen se recorta a 4:5 en pantallas pequeñas."},
    ]
    for ev in events:
        ctrl.tracker.on_event(ev)
    for sid, model, ctx, cost in (("d1", "Opus 5.5", 34, 1.27), ("d2", "Sonnet 5.5", 61, 0.42), ("d3", "Opus 5.5", 82, 2.10)):
        ctrl.tracker.on_status({"session_id": sid, "model": {"display_name": model},
                                "context_window": {"used_percentage": ctx}, "cost": {"total_cost_usd": cost}})
    ctrl.tracker.s["d2"]["updated"] = now_ms() - 4 * 60_000
    ctrl.tracker.s["d3"]["updated"] = now_ms() - 12 * 60_000
    ctrl.usage_state.data = {"five_hour": {"pct": 23.5, "resets": t + 7980},
                             "seven_day": {"pct": 71.2, "resets": t + 300000}, "updated": t - 20}
    ctrl.usageChanged.emit()
    if "--long" in sys.argv:      # frase larga para revisar que el globo crezca bien
        ctrl._say = ("Esta es una frase bastante larga para comprobar que el globo de diálogo crece "
                     "hacia abajo y el texto nunca se sale de él, aunque ocupe varias líneas.", time.time() + 60)
        ctrl.summaryChanged.emit()
        ctrl._new_request("demo-c", {
            "session_id": "d4", "hook_event_name": "PermissionRequest",
            "cwd": f"{home}/un-proyecto-con-un-nombre-muy-largo-para-probar-los-textos",
            "tool_name": "mcp__servidor-de-integracion-continua-corporativo__ejecutar_pipeline_completo_con_despliegue",
            "tool_input": {"rama": "feature/una-rama-con-nombre-larguisimo", "entorno": "staging"}})
    if "--question" in sys.argv:
        ctrl._new_question("demo-q", {
            "session_id": "d1", "hook_event_name": "PreToolUse", "cwd": f"{home}/webapp",
            "tool_name": "AskUserQuestion", "tool_input": {"questions": [
                {"question": "¿Qué librería uso para las fechas?", "header": "Fechas", "multiSelect": False,
                 "options": [{"label": "date-fns", "description": "Funciones sueltas, liviana"},
                             {"label": "Day.js", "description": "API parecida a Moment, muy pequeña"},
                             {"label": "Luxon", "description": "Buen manejo de zonas horarias"}]},
                {"question": "¿Qué pruebas agrego?", "header": "Tests", "multiSelect": True,
                 "options": [{"label": "Unitarias"}, {"label": "Integración"}, {"label": "E2E"}]}]}})
    if "--usage" in sys.argv:
        ctrl.panel.setProperty("view", "usage")
    if "--history" in sys.argv:
        ctrl.panel.setProperty("view", "history")
    if "--pet-edit" in sys.argv:
        ctrl.panel.setProperty("view", "settings")
    if "--pet" in sys.argv:
        ctrl.panel.setProperty("view", "pet")
    ctrl._new_request("demo-a", {
        "session_id": "d2", "hook_event_name": "PermissionRequest", "cwd": f"{home}/api-gateway",
        "tool_name": "Bash", "tool_input": {"command": "git push origin feature/rate-limit", "description": "Sube la rama con el arreglo"},
        "permission_suggestions": [{"type": "addRules", "rules": [{"toolName": "Bash", "ruleContent": "git push:*"}],
                                    "behavior": "allow", "destination": "localSettings"}]})
    ctrl._new_request("demo-b", {
        "session_id": "d1", "hook_event_name": "PermissionRequest", "cwd": f"{home}/webapp",
        "tool_name": "Edit", "tool_input": {"file_path": f"{home}/webapp/src/payments/charge.ts",
                                            "old_string": "const total = amount * rate;",
                                            "new_string": "const total = Math.round(amount * rate * 100) / 100;"}})
    ctrl._show_info({"sid": "d3", "kind": "done", "title": "landing terminó",
                     "body": "Listo: el hero ahora usa clamp() para el título y la imagen se recorta a 4:5."})
    if ctrl.toastPosition != "bubble" and "--question" not in sys.argv:   # el panel taparia las burbujas o la pregunta
        ctrl.panel.setProperty("autoHide", False)
        ctrl.openPanel(at_cursor=False)
        if "--scroll" in sys.argv:
            flick = ctrl.panel.findChild(QObject, "flick")
            QTimer.singleShot(500, lambda: flick.setProperty(
                "contentY", flick.property("contentHeight") - flick.property("height")))
