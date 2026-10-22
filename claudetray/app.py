import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

from PySide6.QtCore import Property, QObject, QPoint, QTimer, QUrl, Signal, Slot, qInstallMessageHandler
from PySide6.QtGui import QAction, QActionGroup, QCursor, QFontDatabase, QGuiApplication, QFont
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config, focus, glass, sound, workarea
from .hotkeys import GlobalHotkeys, is_x11
from .bridge import Bridge, another_instance_running
from .describe import describe
from .history import History
from .usagehist import DailyUsage
from .pet import FOODS, LEGACY_ACCESSORIES, PetState, compute_mood, pet_line, reaction
from .icon import pet_icon, tray_icon
from .listmodel import DictListModel
from .state import SessionTracker, Usage, now_ms

QML = Path(__file__).resolve().parent / "qml"
SESSION_ROLES = ["sid", "pid", "cwd", "project", "title", "state", "activity", "prompt",
                 "message", "modelName", "ctx", "cost", "updated", "pending"]
PENDING_ROLES = ["id", "sid", "project", "kind", "tool", "title", "subtitle", "body", "bodyKind",
                 "danger", "canAlways", "alwaysHint", "created", "timeout", "questions"]
SHADOW = 22          # margen transparente alrededor de cada tarjeta, para la sombra
GAP = 10
TAIL = 10            # alto del pico de la burbuja
MAX_TOASTS = 4
XCB_TYPE_NOTIFICATION = 0x000800   # QXcbWindow::Notification
XCB_TYPE_POPUP_MENU = 0x000200
MAX_PENDING = 30                   # mas solicitudes abiertas que esto: se devuelven a la terminal
log = logging.getLogger("claude-tray")


def _kde_dark():
    text = (Path.home() / ".config" / "kdeglobals").read_text()
    block = text.split("[Colors:Window]", 1)[1]
    for line in block.splitlines()[1:]:
        if line.startswith("["):
            break
        if line.startswith("BackgroundNormal="):
            r, g, b = (int(v) for v in line.split("=", 1)[1].split(",")[:3])
            return (0.299 * r + 0.587 * g + 0.114 * b) < 128
    raise ValueError("sin color de ventana")


def _gnome_dark():
    gs = shutil.which("gsettings")
    if not gs:
        raise ValueError("sin gsettings")
    def get(key):
        return subprocess.run([gs, "get", "org.gnome.desktop.interface", key], capture_output=True,
                              text=True, timeout=2).stdout.strip().strip("'")
    scheme = get("color-scheme")
    if scheme == "prefer-dark":
        return True
    if scheme == "prefer-light":
        return False
    theme = get("gtk-theme")
    if not theme:
        raise ValueError("sin tema")
    return "dark" in theme.lower()


def system_dark():
    """Tema claro u oscuro del escritorio: KDE, GNOME (y derivados) o lo que informe Qt."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    order = [_kde_dark, _gnome_dark] if "KDE" in desktop else [_gnome_dark, _kde_dark]
    for probe in order:
        try:
            return probe()
        except (OSError, IndexError, ValueError, subprocess.SubprocessError):
            continue
    try:
        from PySide6.QtCore import Qt
        scheme = QGuiApplication.styleHints().colorScheme()
        if scheme != Qt.ColorScheme.Unknown:
            return scheme == Qt.ColorScheme.Dark
    except Exception:
        pass
    return True


def theme(dark):
    if dark:
        return {
            "dark": True,
            "tint": "#661C1C1E", "tintStrong": "#8C1C1C1E",
            "stroke": "#26FFFFFF", "rim": "#59FFFFFF", "sheen": "#12FFFFFF",
            "fill": "#0FFFFFFF", "fillHover": "#1CFFFFFF", "fillPress": "#29FFFFFF",
            "text": "#F5F5F7", "text2": "#A6F5F5F7", "text3": "#6BF5F5F7",
            "code": "#40000000", "shadow": "#66000000",
        }
    return {
        "dark": False,
        "tint": "#B3F5F5F7", "tintStrong": "#E0F5F5F7",
        "stroke": "#14000000", "rim": "#B3FFFFFF", "sheen": "#40FFFFFF",
        "fill": "#0A000000", "fillHover": "#14000000", "fillPress": "#21000000",
        "text": "#1D1D1F", "text2": "#A61D1D1F", "text3": "#6B1D1D1F",
        "code": "#0D000000", "shadow": "#2E000000",
    }


class Controller(QObject):
    usageChanged = Signal()
    summaryChanged = Signal()
    notifyDoneChanged = Signal()
    toastPositionChanged = Signal()
    petChanged = Signal()
    mutedChanged = Signal()
    soundsChanged = Signal()
    shortcutsChanged = Signal()
    _hotkey = Signal(str)          # lo emite el hilo de los atajos; se atiende en el hilo principal
    historyChanged = Signal()
    petStateChanged = Signal()
    dailyChanged = Signal()
    _dailyDone = Signal()          # lo emite el hilo de lectura; se atiende en el hilo principal

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.cfg = config.load()
        self.tracker = SessionTracker()
        self.usage_state = Usage()
        self.history = History()
        self.petstate = PetState()
        self.daily = DailyUsage()
        self._daily_busy = False
        self._daily_cache = {}
        self.sessions = DictListModel("sid", SESSION_ROLES, self)
        self.pending = DictListModel("id", PENDING_ROLES, self)
        self._req = {}            # id de conexion -> {"item", "suggestions"}
        self._toasts = {}         # id -> ventana
        self._toast_order = []
        self._panel_hidden_at = 0.0
        self._angle = 0.0
        self._blur_jobs = {}
        self._laying_out = False
        self.hotkeys = None              # se registran despues de crear la bandeja
        self._phase = 0
        self._tray_key = None
        self._last_done = (0.0, "", False)   # (cuando, proyecto, fue larga) del ultimo "terminado"
        self._last_fail = 0.0
        self._say = ("", 0.0, "")             # frase puntual de la mascota (texto, hasta, "action"|"react")
        self._position_override = None   # --bubble/--corner en pruebas: nunca se guarda

        self.bridge = Bridge(config.SOCKET_PATH, self)
        self.bridge.message.connect(self._on_message)
        self.bridge.closed.connect(self._on_closed)

        self.engine = QQmlApplicationEngine()
        ctx = self.engine.rootContext()
        ctx.setContextProperty("ctrl", self)
        ctx.setContextProperty("sessionModel", self.sessions)
        ctx.setContextProperty("pendingModel", self.pending)
        ctx.setContextProperty("T", theme(system_dark()))
        ctx.setContextProperty("MONO", self._mono_font())
        self.engine.load(QUrl.fromLocalFile(str(QML / "Panel.qml")))
        if not self.engine.rootObjects():
            raise SystemExit("No se pudo cargar Panel.qml")
        self.panel = self.engine.rootObjects()[0]
        self.panel.visibleChanged.connect(self._panel_visibility)
        self._toast_comp = QQmlComponent(self.engine, QUrl.fromLocalFile(str(QML / "Toast.qml")))
        if self._toast_comp.isError():
            raise SystemExit("\n".join(e.toString() for e in self._toast_comp.errors()))

        self._build_tray()
        self._hotkey.connect(lambda action: self.control(action))
        if self.cfg.get("global_shortcuts", True):
            binds = {**config.DEFAULTS["shortcuts"], **(self.cfg.get("shortcuts") or {})}
            self.hotkeys = GlobalHotkeys(binds, self._hotkey.emit)
            self.hotkeys.start()
            self.shortcutsChanged.emit()

        self._scan = QTimer(self, interval=2000, timeout=self._rescan)
        self._scan.start()
        self._dailyDone.connect(self._daily_ready)
        self._daily_timer = QTimer(self, interval=3 * 60 * 1000, timeout=self.refreshDaily)
        self._daily_timer.start()
        QTimer.singleShot(1500, self.refreshDaily)
        self._daily_ready(from_worker=False)   # lo que ya estaba en cache, al instante
        self._anim = QTimer(self, interval=140, timeout=self._tray_frame)
        self._anim.start()
        self._rescan()

    @staticmethod
    def _mono_font():
        families = set(QFontDatabase.families())
        for fam in ("JetBrains Mono", "FiraCode Nerd Font Mono", "Fira Code", "DejaVu Sans Mono"):
            if fam in families:
                return fam
        return "monospace"

    # --- bandeja ---------------------------------------------------------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(tray_icon(), self)
        self.tray.setToolTip("Claude Code")
        menu = QMenu()
        open_action = QAction("Abrir panel", menu, triggered=lambda: self.openPanel())
        self._done_action = QAction("Avisar cuando una sesión termine", menu, checkable=True)
        self._done_action.setChecked(bool(self.cfg.get("notify_done")))
        self._done_action.toggled.connect(self._set_notify_done)
        quit_action = QAction("Salir", menu, triggered=self.quit)
        for a in (open_action, self._done_action):
            menu.addAction(a)
        where = menu.addMenu("Notificaciones")
        group = QActionGroup(where)
        self._position_actions = {}
        for key, label in (("corner", "En la esquina superior"), ("bubble", "Burbuja sobre el icono")):
            act = QAction(label, where, checkable=True)
            act.setChecked(self._toast_position() == key)
            act.triggered.connect(lambda _=False, key=key: self.setToastPosition(key))
            group.addAction(act)
            where.addAction(act)
            self._position_actions[key] = act
        mute = menu.addMenu("Silenciar")
        for label, minutes in (("30 minutos", 30), ("1 hora", 60), ("Hasta mañana (8:00)", -2),
                               ("Hasta que lo reactive", -1)):
            mute.addAction(QAction(label, mute, triggered=lambda _=False, m=minutes: self.setMute(m)))
        mute.addSeparator()
        mute.addAction(QAction("Reactivar avisos", mute, triggered=lambda: self.setMute(0)))
        menu.aboutToShow.connect(self._remember_anchor)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._remember_anchor()
            self.togglePanel()

    def _remember_anchor(self):
        """KDE no informa donde esta el icono: se recuerda donde lo clicaste."""
        pos = QCursor.pos()
        old = self.cfg.get("tray_anchor")
        if not old or abs(old[0] - pos.x()) > 3 or abs(old[1] - pos.y()) > 3:
            self.cfg["tray_anchor"] = [pos.x(), pos.y()]
            config.save(self.cfg)
            self._layout_toasts()

    def _tray_anchor(self):
        saved = self.cfg.get("tray_anchor")
        if saved and QGuiApplication.screenAt(QPoint(*saved)):
            return QPoint(*saved)
        screen = QGuiApplication.primaryScreen()
        g, a = screen.geometry(), workarea.available(screen)
        # Estimacion hasta el primer clic: junto al reloj, en el borde del panel.
        y = g.bottom() - 20 if a.bottom() < g.bottom() else g.top() + 20
        return QPoint(a.right() - 200, y)

    def _toast_position(self):
        pos = self._position_override or self.cfg.get("toast_position")
        return "bubble" if pos == "bubble" else "corner"

    @Slot(str)
    def setToastPosition(self, key):
        if key not in ("corner", "bubble"):
            return
        self._position_override = None
        self.cfg["toast_position"] = key
        config.save(self.cfg)
        if key in getattr(self, "_position_actions", {}):
            self._position_actions[key].setChecked(True)
        self.toastPositionChanged.emit()
        self._layout_toasts()

    def _mood_info(self):
        rows = self.sessions.items()
        busy = [r for r in rows if r["state"] == "working"]
        waiting = [r for r in rows if r["state"] == "waiting"]
        pend_all = [r["item"] for r in self._req.values()]
        pend = [i for i in pend_all if i["kind"] == "permission"]
        asks = [i for i in pend_all if i["kind"] == "question"]
        last_event = max((r["updated"] for r in rows), default=0) / 1000
        five = self.usage_state.view()["five_hour"]["pct"]
        mood, emote = compute_mood(
            time.time(), self.petstate, sessions=len(rows), working=len(busy),
            thinking_only=bool(busy) and all(r["activity"] == "Pensando…" for r in busy),
            waiting=len(waiting) + len(asks), pending=len(pend), danger=any(i["danger"] for i in pend),
            last_done=self._last_done[0], last_done_long=self._last_done[2], last_fail=self._last_fail,
            last_event=last_event, usage_5h=five)
        project = (pend[0]["project"] if pend else asks[0]["project"] if asks else waiting[0]["project"] if waiting
                   else busy[0]["project"] if busy else "")
        return mood, emote, {"pending": len(pend), "project": project, "done_project": self._last_done[1],
                             "working_n": len(busy), "usage_5h": five}

    def _mood(self):
        return self._mood_info()[0]

    def _refresh_tray(self):
        rows = self.sessions.items()
        waiting = sum(1 for r in rows if r["state"] == "waiting")
        working = sum(1 for r in rows if r["state"] == "working")
        self._tray_frame(force=True)
        parts = [f"{len(rows)} sesión" + ("es" if len(rows) != 1 else "")]
        if working:
            parts.append(f"{working} trabajando")
        if waiting:
            parts.append(f"{waiting} te espera" + ("n" if waiting > 1 else ""))
        if self._muted():
            parts.append("🔕 " + self._mute_label().lower())
        self.tray.setToolTip(f"{self._pet()['name']} · " + " · ".join(parts))

    def _tray_frame(self, force=False):
        """Avanza la animacion del icono; solo lo repinta si el cuadro cambia."""
        self._phase += 1
        mood, emote, _ = self._mood_info()
        pet, muted = self._pet(), self._muted()
        if pet["tray"] == "glyph":
            spin = mood == "working"
            self._angle = (self._angle + 6) % 360 if spin else 0.0
            key = ("glyph", self._angle, mood == "waiting", not self.sessions.count, muted)
            make = lambda: tray_icon(self._angle, badge=mood == "waiting", dim=not self.sessions.count, muted=muted)
        else:
            speed = {"working": 2, "thinking": 3, "waiting": 3, "happy": 1, "celebrate": 1, "sleep": 6,
                     "tired": 5, "bored": 5, "hungry": 4, "worried": 2, "eat": 1, "play": 1, "love": 2}.get(mood, 1)
            phase = (self._phase // speed) % 24
            if mood == "idle":          # quieto, con un parpadeo de vez en cuando
                phase = 0 if phase == 0 else 1
            key = ("pet", mood, emote, phase, pet["color"], muted)
            make = lambda: pet_icon(mood, phase, pet["color"], muted=muted, emote=emote)
        if force or key != self._tray_key:
            self._tray_key = key
            self.tray.setIcon(make())

    # --- consumo por dia ----------------------------------------------------------
    @Slot()
    def refreshDaily(self):
        if self._daily_busy:
            return
        self._daily_busy = True

        def run():
            try:
                self.daily.refresh()
            except Exception:                 # un registro raro no debe tumbar la app
                log.error("No se pudo leer el consumo diario:\n%s", traceback.format_exc())
            self._dailyDone.emit()

        threading.Thread(target=run, daemon=True).start()

    def _daily_ready(self, from_worker=True):
        if from_worker:
            self._daily_busy = False
        self._daily_cache = {n: {"rows": self.daily.series(n), "summary": self.daily.summary(n)} for n in (7, 30)}
        self.dailyChanged.emit()
        self.summaryChanged.emit()

    @Slot(int, result="QVariantList")
    def usageSeries(self, days):
        return (self._daily_cache.get(days) or {}).get("rows", [])

    @Slot(int, result="QVariantMap")
    def usageSummary(self, days):
        return (self._daily_cache.get(days) or {}).get("summary", {})

    # --- silencio ---------------------------------------------------------------
    def _muted(self):
        until = self.cfg.get("muted_until", 0)
        return until == -1 or until > time.time()

    @Slot(int)
    def setMute(self, minutes):
        """minutes: 0 reactiva, -1 indefinido, -2 hasta mañana a las 8:00."""
        if minutes == 0:
            until = 0
        elif minutes == -1:
            until = -1
        elif minutes == -2:
            t = time.localtime()
            until = time.mktime((t.tm_year, t.tm_mon, t.tm_mday + 1, 8, 0, 0, 0, 0, -1))
        else:
            until = time.time() + minutes * 60
        self.cfg["muted_until"] = until
        config.save(self.cfg)
        self.mutedChanged.emit()
        self._refresh_tray()

    def _mute_label(self):
        until = self.cfg.get("muted_until", 0)
        if until == -1:
            return "Silenciado"
        if until > time.time():
            return "Silenciado hasta las " + time.strftime("%H:%M", time.localtime(until))
        return ""

    # --- mascota ---------------------------------------------------------------
    def _pet(self):
        pet = {**config.DEFAULTS["pet"], **(self.cfg.get("pet") or {})}
        pet["accessory"] = LEGACY_ACCESSORIES.get(pet["accessory"], pet["accessory"])
        return pet

    @Slot(str, str)
    def setPet(self, key, value):
        pet = self._pet()
        if key == "name":
            value = value.strip()[:18] or "Clawd"
        if key == "accessory" and value not in self.petstate.unlocked():
            return
        pet[key] = value
        self.cfg["pet"] = pet
        config.save(self.cfg)
        self.petChanged.emit()
        self.summaryChanged.emit()
        self._tray_frame(force=True)

    def _pet_action(self, ok_phrase):
        ok, phrase = ok_phrase
        self._say = (phrase, time.time() + 4, "action")
        self.petStateChanged.emit()
        self.summaryChanged.emit()
        self._tray_frame(force=True)

    def _react(self, kind, project=""):
        """La mascota comenta lo que acaba de pasar (aprobar, rechazar, nueva sesion…)."""
        text = reaction(kind, time.time(), project)
        if text:
            self._say = (text, time.time() + 5, "react")
            self.summaryChanged.emit()

    @Slot(str)
    def feedPet(self, food):
        self._pet_action(self.petstate.feed(food, time.time()))

    @Slot()
    def playPet(self):
        self._pet_action(self.petstate.play(time.time()))

    @Slot()
    def caressPet(self):
        self._pet_action(self.petstate.caress(time.time()))

    def _set_notify_done(self, on):
        self.cfg["notify_done"] = on
        config.save(self.cfg)
        self.notifyDoneChanged.emit()

    # --- mensajes de los hooks ---------------------------------------------
    def _on_message(self, msg, cid):
        """Un mensaje raro nunca debe tumbar la app ni dejar a Claude esperando."""
        try:
            self._handle_message(msg, cid)
        except Exception:
            log.error("Error procesando un mensaje del hook:\n%s", traceback.format_exc())
            if isinstance(msg, dict) and msg.get("kind") in ("permission", "question"):
                self._req.pop(cid, None)
                self.bridge.reply(cid, {})         # sin decision: Claude pregunta en la terminal

    def _handle_message(self, msg, cid):
        if not isinstance(msg, dict):
            return
        kind, data = msg.get("kind"), msg.get("data") or {}
        if not isinstance(data, dict):
            return
        if kind == "status":
            self.tracker.on_status(data)
            if data.get("rate_limits"):
                self.usage_state.on_status(data)
                self.usageChanged.emit()
            self._publish()
        elif kind == "event":
            notice = self.tracker.on_event(data)
            if data.get("hook_event_name") == "Stop":
                sess = self.tracker.s.get(data.get("session_id"), {})
                long_task = bool(notice and notice.get("long"))
                self._last_done = (time.time(), sess.get("project", ""), long_task)
                self.petstate.on_done(long_task)
                self.petStateChanged.emit()
                self.history.add("done", sid=data.get("session_id"), project=sess.get("project", ""))
                self.historyChanged.emit()
            ev = data.get("hook_event_name")
            sess_now = self.tracker.s.get(data.get("session_id"), {})
            if ev == "SessionStart" and data.get("source") == "startup":
                self._react("start", sess_now.get("project", ""))
            elif ev == "UserPromptSubmit":
                self._react("prompt", sess_now.get("project", ""))
            if ev == "StopFailure":
                self._last_fail = time.time()
                self._ping("fail")
            elif ev == "Stop":
                self._ping("done")
            if ev in ("UserPromptSubmit", "Stop", "SessionEnd", "StopFailure"):
                self._drop_session_requests(data.get("session_id"))
            elif ev == "PostToolUse":       # la herramienta ya corrio: se aprobo en la terminal
                self._drop_session_requests(data.get("session_id"), data.get("tool_name"), data.get("tool_input"))
            self._publish()
            if notice and self.cfg.get("notify_done") and not self._muted() and not self._toast_for_session(notice["sid"]):
                self._show_info(notice)
        elif kind == "control":
            ok, message = self.control(str(msg.get("action", "")))
            self.bridge.reply(cid, {"ok": ok, "message": message})
        elif kind in ("permission", "question") and len(self._req) >= MAX_PENDING:
            log.warning("Demasiadas solicitudes abiertas; esta se devuelve a la terminal")
            self.bridge.reply(cid, {})
        elif kind == "permission":
            if data.get("tool_name") == "AskUserQuestion":
                self.bridge.reply(cid, {"decision": None})   # las preguntas van por su propio hook
            else:
                self._new_request(cid, data)
        elif kind == "question":
            self._new_question(cid, data)

    def _new_request(self, cid, data):
        sid = data.get("session_id", "")
        self.tracker.on_event(data)
        sess = self.tracker.s.get(sid, {})
        tool = data.get("tool_name", "")
        info = describe(tool, data.get("tool_input"), data.get("cwd", ""))
        suggestions = data.get("permission_suggestions") or []
        hint = ""
        for sug in suggestions:
            for rule in sug.get("rules", []):
                hint = f"{rule.get('toolName', '')}({rule.get('ruleContent', '')})" if rule.get("ruleContent") else rule.get("toolName", "")
                break
            if hint:
                break
        item = {
            "id": cid, "sid": sid, "project": sess.get("project") or os.path.basename(data.get("cwd", "")),
            "kind": "permission", "tool": tool, **info,
            "canAlways": bool(suggestions) and not info["danger"], "alwaysHint": hint,
            "created": now_ms(), "timeout": int(self.cfg.get("approval_timeout", 540)), "questions": [],
        }
        self._req[cid] = {"item": item, "suggestions": suggestions, "input": data.get("tool_input")}
        self._publish()
        if not self._muted():          # silenciado: la solicitud queda solo en el panel
            self._show_toast(item, "permission")
        self._ping("permission")

    def _new_question(self, cid, data):
        """AskUserQuestion: Claude pregunta con opciones y la respuesta se elige en la app."""
        sid = data.get("session_id", "")
        self.tracker.on_event(data)
        sess = self.tracker.s.get(sid, {})
        tool_input = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
        questions = [q for q in tool_input.get("questions") or [] if isinstance(q, dict) and q.get("question")]
        if not questions or self._muted():     # silenciado: la pregunta va directo a la terminal
            self.bridge.reply(cid, {})
            return
        item = {
            "id": cid, "sid": sid, "project": sess.get("project") or os.path.basename(data.get("cwd", "")),
            "kind": "question", "tool": "AskUserQuestion",
            "title": "Pregunta" if len(questions) == 1 else f"{len(questions)} preguntas",
            "subtitle": questions[0].get("question", ""), "body": "", "bodyKind": "text",
            "danger": False, "canAlways": False, "alwaysHint": "",
            "created": now_ms(), "timeout": int(self.cfg.get("approval_timeout", 540)),
            "questions": questions,
        }
        self._req[cid] = {"item": item, "suggestions": [], "input": data.get("tool_input")}
        self._publish()
        if not self._muted():
            self._show_toast(item, "question")
        self._ping("question")

    def _on_closed(self, cid):
        req = self._req.get(cid)
        if req:   # el hook se cerro: se respondio en la terminal, o vencio su espera
            waited = now_ms() - req["item"]["created"]
            timed_out = waited >= (req["item"]["timeout"] - 3) * 1000
            self._resolve(cid, None, reply=False, outcome="timeout" if timed_out else "elsewhere")

    def _drop_session_requests(self, sid, tool=None, tool_input=None):
        for cid, req in list(self._req.items()):
            if req["item"]["sid"] != sid:
                continue
            if tool is None:
                self._resolve(cid, None, outcome="dropped")
            elif req["item"]["tool"] == tool and (req["input"] == tool_input or tool == "AskUserQuestion"):
                self._resolve(cid, None, outcome="elsewhere")

    def _resolve(self, cid, decision, reply=True, outcome="elsewhere", payload=None, detail=None):
        req = self._req.pop(cid, None)
        if req is None:
            return
        item = req["item"]
        if detail is None:
            detail = item["subtitle"] if item["tool"] != "Bash" else (item["body"].splitlines() or [""])[0]
        self.history.add("decision", outcome=outcome, sid=item["sid"], project=item["project"],
                         tool=item["tool"], title=item["title"], detail=detail[:300], danger=item["danger"])
        self.historyChanged.emit()
        if outcome in ("allow", "always"):
            self.petstate.on_approval()
            self.petStateChanged.emit()
        if outcome in ("allow", "always", "deny", "answered"):
            self._react(outcome, item["project"])
        if reply:
            self.bridge.reply(cid, payload if payload is not None else {"decision": decision})
        self._close_toast(cid)
        self._publish()

    def _publish(self):
        counts = {}
        for req in self._req.values():
            counts[req["item"]["sid"]] = counts.get(req["item"]["sid"], 0) + 1
        self.tracker.set_pending(counts)
        self.sessions.sync(self.tracker.listing())
        self.pending.sync(sorted((r["item"] for r in self._req.values()), key=lambda i: i["created"]))
        self.summaryChanged.emit()
        self._refresh_tray()

    def _rescan(self):
        until = self.cfg.get("muted_until", 0)
        if until > 0 and time.time() >= until:
            self.setMute(0)
        self.tracker.scan_files()
        now = time.time()
        rows = self.sessions.items()
        self.petstate.tick(now, sessions=len(rows), working=sum(r["state"] == "working" for r in rows))
        self.petstate.maybe_save(now)
        self.petStateChanged.emit()
        self._publish()

    def _ping(self, kind="permission"):
        """Sonido elegido para ese tipo de aviso, salvo que la app este silenciada."""
        name = self._sounds().get(kind, "")
        if name and not self._muted():
            sound.play(name, self.cfg.get("sound_volume", 70))

    def _sounds(self):
        return sound.normalize(self.cfg.get("sounds"))

    @Slot(str, str)
    def setSound(self, kind, name):
        if kind not in sound.DEFAULTS or (name and name not in sound.NAMES):
            return
        sounds = self._sounds()
        sounds[kind] = name
        self.cfg["sounds"] = sounds
        config.save(self.cfg)
        self.soundsChanged.emit()
        if name:
            sound.play(name, self.cfg.get("sound_volume", 70))      # se escucha al elegirlo

    @Slot(int)
    def setSoundVolume(self, volume):
        self.cfg["sound_volume"] = max(0, min(100, int(volume)))
        config.save(self.cfg)
        self.soundsChanged.emit()

    @Slot(str)
    def previewSound(self, name):
        sound.play(name, self.cfg.get("sound_volume", 70))

    # --- notificaciones flotantes -------------------------------------------
    def _toast_for_session(self, sid):
        return any(r["item"]["sid"] == sid for r in self._req.values())

    def _show_info(self, notice):
        nid = f"info-{now_ms()}"
        item = {"id": nid, "sid": notice["sid"], "kind": notice["kind"],
                "title": notice["title"], "body": notice["body"][:400]}
        self._show_toast(item, "info")

    def _show_toast(self, item, mode):
        win = self._toast_comp.createWithInitialProperties(
            {"item": item, "mode": mode, "bubble": self._toast_position() == "bubble"})
        if win is None:
            log.error("No se pudo crear la notificación: %s", "; ".join(e.toString() for e in self._toast_comp.errors()))
            return
        # Tipo Notification en X11: KWin no la esconde aunque la app no este activa
        # (con Qt.Tool a secas seria "utility" y se ocultaria).
        win.setProperty("_q_xcb_wm_window_type", XCB_TYPE_NOTIFICATION)
        self._toasts[item["id"]] = win
        self._toast_order.append(item["id"])
        win.heightChanged.connect(self._layout_toasts)
        self._layout_toasts()

    def _close_toast(self, tid):
        win = self._toasts.get(tid)
        if win is not None:
            win.setProperty("closing", True)

    def _layout_toasts(self):
        if self._laying_out:
            return
        self._laying_out = True
        try:
            live = [t for t in self._toast_order
                    if t in self._toasts and not self._toasts[t].property("closing")]
            bubble = self._toast_position() == "bubble"
            for tid in live:
                self._toasts[tid].setProperty("bubble", bubble)
            (self._layout_bubbles if bubble else self._layout_corner)(live)
            # En modo burbuja el panel ocupa el mismo lugar: mientras este abierto,
            # las solicitudes se ven ahi y las burbujas se esconden.
            hide = bubble and bool(self.panel.property("visible"))
            for tid in live:
                win = self._toasts[tid]
                if hide and win.isVisible():
                    win.hide()
                elif not hide and not win.isVisible():
                    win.show()
        finally:
            self._laying_out = False

    def _layout_corner(self, live):
        screen = workarea.available(QGuiApplication.primaryScreen())
        y = screen.top() + GAP - SHADOW
        for i, tid in enumerate(live):
            win = self._toasts[tid]
            win.setProperty("targetX", screen.right() + 1 - win.width() - GAP + SHADOW)
            win.setProperty("targetY", y)
            win.setProperty("showTail", False)
            win.setProperty("hiddenByStack", i >= MAX_TOASTS)
            y += win.height() - 2 * SHADOW + GAP

    def _layout_bubbles(self, live):
        anchor = self._tray_anchor()
        screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        a = workarea.available(screen)
        down = anchor.y() > a.center().y()          # bandeja abajo: el pico apunta hacia abajo
        edge = a.bottom() + 1 - 4 if down else a.top() + 4
        cursor = edge - TAIL if down else edge + TAIL  # borde de la tarjeta mas cercana al icono
        for i, tid in enumerate(reversed(live)):    # la mas nueva queda pegada al icono
            win = self._toasts[tid]
            card_w = win.width() - 2 * SHADOW
            card_h = win.height() - 2 * SHADOW - TAIL
            x = anchor.x() - win.width() // 2
            x = max(a.left() + GAP - SHADOW, min(x, a.right() + 1 - GAP - SHADOW - card_w))
            if down:
                top = cursor - card_h
                y = top - SHADOW
                cursor = top - GAP
            else:
                y = cursor - SHADOW - TAIL
                cursor = cursor + card_h + GAP
            win.setProperty("targetX", x)
            win.setProperty("targetY", y)
            win.setProperty("tailDir", 1 if down else -1)
            win.setProperty("tailX", anchor.x() - x)
            win.setProperty("showTail", i == 0)
            win.setProperty("hiddenByStack", i >= MAX_TOASTS)

    @Slot(str)
    def toastGone(self, tid):
        win = self._toasts.pop(tid, None)
        if tid in self._toast_order:
            self._toast_order.remove(tid)
        if win is not None:
            win.deleteLater()
        self._layout_toasts()

    @Slot(str)
    def dismissToast(self, tid):
        self._close_toast(tid)

    # --- acciones desde QML ------------------------------------------------
    @Slot(str)
    def allow(self, cid):
        self._resolve(cid, {"behavior": "allow"}, outcome="allow")

    @Slot(str)
    def allowAlways(self, cid):
        req = self._req.get(cid)
        if req:
            self._resolve(cid, {"behavior": "allow", "updatedPermissions": req["suggestions"]}, outcome="always")

    @Slot(str)
    def deny(self, cid):
        self._resolve(cid, {"behavior": "deny", "message": "El usuario rechazó esta acción desde Claude Tray."},
                      outcome="deny")

    # --- atajos / comandos externos -------------------------------------------
    def _latest(self, kind=None):
        reqs = [r["item"] for r in self._req.values() if kind is None or r["item"]["kind"] == kind]
        return max(reqs, key=lambda i: i["created"]) if reqs else None

    def control(self, action):
        """Acciones de los atajos y de `claude-tray --allow` etc. Devuelve (ok, mensaje)."""
        if action == "panel":
            self.togglePanel_from_shortcut()
            return True, "Panel"
        if action in ("allow", "deny"):
            item = self._latest("permission")
            if item is None:
                return False, "No hay solicitudes de permiso pendientes."
            if action == "allow" and item["danger"]:
                # un atajo nunca aprueba algo destructivo: eso exige mantener el boton presionado
                self._say = ("Esa es delicada: apruébala desde la notificación.", time.time() + 5, "action")
                self.summaryChanged.emit()
                return False, "Es un comando destructivo: apruébalo desde la notificación."
            (self.allow if action == "allow" else self.deny)(item["id"])
            return True, f"{'Permitido' if action == 'allow' else 'Rechazado'}: {item['title']} en {item['project']}"
        if action == "terminal":
            item = self._latest()
            if item is None:
                return False, "No hay nada pendiente."
            self.toTerminal(item["id"])
            return True, f"Enviado a la terminal: {item['title']}"
        return False, f"Acción desconocida: {action}"

    def togglePanel_from_shortcut(self):
        if self.panel.property("visible"):
            self.panel.setProperty("visible", False)
        else:
            self.openPanel(at_cursor=False)

    def _shortcuts_info(self):
        binds = {**config.DEFAULTS["shortcuts"], **(self.cfg.get("shortcuts") or {})}
        hk = self.hotkeys
        return {
            "x11": is_x11(),
            "enabled": bool(self.cfg.get("global_shortcuts", True)),
            "items": [{"action": a, "keys": k,
                       "active": bool(hk and a in hk.active),
                       "reason": (hk.failed.get(a, "") if hk else "desactivados")} for a, k in binds.items()],
        }

    @Slot(str, "QVariantMap")
    def answerQuestion(self, cid, answers):
        req = self._req.get(cid)
        if not req or not answers:
            return
        answers = {str(k): str(v) for k, v in answers.items()}
        summary = " · ".join(f"{q}: {a}" for q, a in answers.items())
        self._resolve(cid, None, outcome="answered", payload={"answers": answers}, detail=summary[:300])

    @Slot(str)
    def toTerminal(self, cid):
        req = self._req.get(cid)
        sid = req["item"]["sid"] if req else ""
        self._resolve(cid, None, outcome="terminal")
        self.focusSession(sid)

    @Slot(str, result=bool)
    def canMessage(self, sid):
        sess = self.tracker.s.get(sid)
        return bool(sess and sess.get("pid") and focus.can_send(sess["pid"]))

    @Slot(str, str, result=bool)
    def sendToSession(self, sid, text):
        """Escribe un mensaje en la terminal de la sesion y lo envia (Enter un instante despues)."""
        sess = self.tracker.s.get(sid)
        text = " ".join((text or "").split())
        if not sess or not text or not focus.send_text(sess.get("pid"), text):
            return False
        pid = sess["pid"]
        QTimer.singleShot(250, lambda: focus.send_enter(pid))
        self.history.add("message", sid=sid, project=sess["project"], detail=text[:300])
        self._react("message", sess["project"])
        self.historyChanged.emit()
        return True

    @Slot(str)
    def focusSession(self, sid):
        sess = self.tracker.s.get(sid)
        if sess and sess.get("pid"):
            self.panel.setProperty("visible", False)
            focus.focus(sess["pid"])

    @Slot(QObject, float, float, float, float, float, float, float, float)
    def setBlur(self, win, x, y, w, h, r, tail_x, tail_size, tail_dir):
        # Se agrupan los cambios de tamaño de un mismo frame en una sola llamada a xprop.
        key = id(win)
        job = self._blur_jobs.get(key)
        if job is None:
            job = self._blur_jobs[key] = {"timer": QTimer(self, singleShot=True, interval=16)}
            job["timer"].timeout.connect(lambda: glass.apply(*job["args"]))
            win.destroyed.connect(lambda *_: self._blur_jobs.pop(key, None))
        job["args"] = (win, x, y, w, h, r, tail_x, tail_size, tail_dir)
        job["timer"].start()

    @Slot()
    def togglePanel(self):
        if self.panel.property("visible"):
            self.panel.setProperty("visible", False)
        elif time.monotonic() - self._panel_hidden_at > 0.35:
            self.openPanel()

    @Slot()
    def openPanel(self, at_cursor=True):
        screen = QGuiApplication.screenAt(QCursor.pos()) if at_cursor else None
        screen = screen or QGuiApplication.primaryScreen()
        g, a = screen.geometry(), workarea.available(screen)
        pos = QCursor.pos() if at_cursor else self._tray_anchor()
        w = self.panel.width()
        x = min(max(pos.x() - w // 2, a.left() + GAP - SHADOW), a.right() + 1 - w - GAP + SHADOW)
        bottom = not (a.top() > g.top() and a.bottom() >= g.bottom())
        self.panel.setProperty("maxHeight", min(860, a.height() - 2 * GAP))
        self.panel.setProperty("anchorBottom", bottom)
        self.panel.setProperty("anchorEdge", a.bottom() + 1 - GAP + SHADOW if bottom else a.top() + GAP - SHADOW)
        self.panel.setProperty("x", x)
        self.panel.setProperty("visible", True)
        self.panel.raise_()
        self.panel.requestActivate()

    def _panel_visibility(self):
        if not self.panel.property("visible"):
            self._panel_hidden_at = time.monotonic()
        self._layout_toasts()

    @Slot()
    def quit(self):
        for cid in list(self._req):
            self._resolve(cid, None, outcome="quit")
        self.petstate.save()
        self.tray.hide()
        self.app.quit()

    # --- propiedades para QML ------------------------------------------------
    def _usage(self):
        return self.usage_state.view()

    def _summary(self):
        rows = self.sessions.items()
        mood, emote, info = self._mood_info()
        now = time.time()
        st, hs = self.petstate, self.history.stats(now)
        line = pet_line(mood, emote, now, **info, streak=hs["streak"], level=st.level,
                        hunger=st.d["hunger"], energy=st.d["energy"], name=self._pet()["name"])
        ratio = (self._daily_cache.get(7) or {}).get("summary", {}).get("ratio", 0)
        if mood == "idle" and ratio >= 1.5 and int(now // 30) % 2:   # se alterna con la frase normal
            line = f"Hoy llevas {ratio:.1f}× tu promedio diario de tokens.".replace(".", ",", 1)
        say, until, kind = self._say          # lo recien dicho gana, salvo que algo te este esperando
        if say and now < until and not (kind == "react" and mood == "waiting"):
            line = say
        if mood in ("eat", "play", "love") and not line:
            line = "…"
        return {
            "total": len(rows),
            "working": sum(1 for r in rows if r["state"] == "working"),
            "waiting": sum(1 for r in rows if r["state"] == "waiting"),
            "cost": round(sum(r["cost"] for r in rows), 2),
            "mood": mood,
            "emote": emote,
            "line": line,
        }

    usage = Property("QVariantMap", _usage, notify=usageChanged)
    summary = Property("QVariantMap", _summary, notify=summaryChanged)
    notifyDone = Property(bool, lambda self: bool(self.cfg.get("notify_done")), notify=notifyDoneChanged)
    toastPosition = Property(str, _toast_position, notify=toastPositionChanged)
    pet = Property("QVariantMap", _pet, notify=petChanged)
    muted = Property(bool, _muted, notify=mutedChanged)
    shortcuts = Property("QVariantMap", _shortcuts_info, notify=shortcutsChanged)
    sounds = Property("QVariantMap", _sounds, notify=soundsChanged)
    soundVolume = Property(int, lambda self: int(self.cfg.get("sound_volume", 70)), notify=soundsChanged)
    canPlaySound = Property(bool, lambda self: sound.available(), constant=True)
    soundLibrary = Property("QVariantList", lambda self: [{"key": k, "label": l} for k, l in sound.LIBRARY], constant=True)
    muteLabel = Property(str, _mute_label, notify=mutedChanged)
    petState = Property("QVariantMap", lambda self: self.petstate.view(time.time()), notify=petStateChanged)
    foods = Property("QVariantList", lambda self: [{"key": k, "name": v[2]} for k, v in FOODS.items()], constant=True)
    dailyRevision = Property(int, lambda self: id(self._daily_cache) % 100000, notify=dailyChanged)
    historyRecent = Property("QVariantList", lambda self: self.history.recent(300), notify=historyChanged)
    historyStats = Property("QVariantMap", lambda self: self.history.stats(), notify=historyChanged)


def setup_logging():
    """Log en ~/.cache/claude-tray/claude-tray.log (rotativo), con errores de Python y de QML."""
    path = config.CACHE_DIR / "claude-tray.log"
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler())
    root.setLevel(logging.INFO)
    sys.excepthook = lambda t, v, tb: log.error("Error no controlado:\n%s", "".join(traceback.format_exception(t, v, tb)))

    def qt_messages(mode, ctx, message):
        if "propertyCache" not in message:      # ruido conocido de Qt
            log.warning("Qt: %s", message)
    qInstallMessageHandler(qt_messages)


CONTROL_FLAGS = {"--allow": "allow", "--deny": "deny", "--panel": "panel", "--terminal": "terminal"}


def send_control(action):
    """`claude-tray --allow` etc.: le pide la accion a la app abierta por el socket."""
    import json
    import socket
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(config.SOCKET_PATH)
        s.sendall((json.dumps({"kind": "control", "action": action}) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        reply = json.loads(buf.split(b"\n")[0] or b"{}")
    except (OSError, ValueError):
        print("Claude Tray no está abierto.")
        return 2
    print(reply.get("message", ""))
    return 0 if reply.get("ok") else 1


def main():
    if "--version" in sys.argv:
        from . import __version__
        print(f"Claude Tray {__version__}")
        return 0
    for flag, action in CONTROL_FLAGS.items():
        if flag in sys.argv:
            try:
                config.secure_runtime()
            except (RuntimeError, OSError) as exc:
                print(exc)
                return 2
            return send_control(action)
    os.umask(0o077)                      # todo lo que crea la app queda solo para su dueño
    config.private_dirs()
    setup_logging()
    # xcb (X11, o XWayland en Wayland) permite ubicar las notificaciones donde corresponde.
    # Si no hay ningun servidor X, Qt elige solo (p. ej. Wayland puro, con posiciones limitadas).
    if os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    QQuickWindow.setDefaultAlphaBuffer(True)
    app = QApplication(sys.argv)
    app.setApplicationName("Claude Tray")
    app.setDesktopFileName("claude-tray")
    app.setQuitOnLastWindowClosed(False)
    if "Inter" in QFontDatabase.families():
        font = QFont("Inter")
        font.setPixelSize(13)
        app.setFont(font)
    try:
        config.secure_runtime()
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1
    if another_instance_running(config.SOCKET_PATH):
        print("Claude Tray ya está abierto.")
        return 0
    no_tray = not QSystemTrayIcon.isSystemTrayAvailable()
    if no_tray:
        log.warning("No se detectó bandeja del sistema (en GNOME hace falta la extensión AppIndicator).")
    ctrl = Controller(app)
    if no_tray:      # sin bandeja (p. ej. GNOME sin AppIndicator): explicar como seguir
        QTimer.singleShot(2500, lambda: ctrl._show_info({
            "sid": "", "kind": "ask", "title": "No encontré la bandeja del sistema",
            "body": "Las notificaciones funcionan igual. Abre el panel con «claude-tray --panel». "
                    "En GNOME, instala la extensión «AppIndicator and KStatusNotifierItem Support»."}))
    if "--bubble" in sys.argv or "--corner" in sys.argv:   # para pruebas: no se guarda
        ctrl._position_override = "bubble" if "--bubble" in sys.argv else "corner"
        ctrl.toastPositionChanged.emit()
    if "--demo" in sys.argv:
        from .demo import load_demo
        QTimer.singleShot(300, lambda: load_demo(ctrl))
    elif "--panel" in sys.argv:
        QTimer.singleShot(400, lambda: ctrl.openPanel(at_cursor=False))
    return app.exec()
