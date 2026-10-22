"""Historial de decisiones y tareas terminadas (JSONL).

Sirve de auditoria (que se aprobo, cuando y donde) y de fuente para las
estadisticas de la mascota.
"""
import json
import time
from datetime import date, timedelta
from pathlib import Path

from .config import DATA_DIR

MAX_ENTRIES = 5000

# Como termino una solicitud de permiso (las etiquetas visibles estan en qml/util.js).
OUTCOMES = {"allow", "always", "deny", "answered", "terminal", "elsewhere", "timeout", "dropped", "quit"}
APPROVED = {"allow", "always"}


def day_key(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts))


class History:
    def __init__(self, path=None):
        self.path = Path(path) if path else DATA_DIR / "history.jsonl"
        self.entries = self._load()

    def _load(self):
        try:
            lines = self.path.read_text().splitlines()
        except OSError:
            return []
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]
            self._rewrite(entries)
        return entries

    def _rewrite(self, entries):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries))
        except OSError:
            pass

    def add(self, kind, ts=None, **fields):
        entry = {"ts": ts if ts is not None else time.time(), "kind": kind, **fields}
        self.entries.append(entry)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass
        if len(self.entries) > MAX_ENTRIES * 1.2:      # recorta de vez en cuando, no en cada linea
            self.entries = self.entries[-MAX_ENTRIES:]
            self._rewrite(self.entries)
        return entry

    def recent(self, n=200):
        return sorted(self.entries[-n:], key=lambda e: e["ts"], reverse=True)

    def stats(self, now=None):
        now = now if now is not None else time.time()
        today = day_key(now)
        out = {"today_allowed": 0, "today_denied": 0, "today_done": 0,
               "allowed": 0, "denied": 0, "done": 0, "streak": 0, "first": 0}
        days = set()
        for e in self.entries:
            kind, d = e.get("kind"), day_key(e["ts"])
            days.add(d)
            if not out["first"] or e["ts"] < out["first"]:
                out["first"] = e["ts"]
            if kind == "decision":
                if e.get("outcome") in APPROVED:
                    out["allowed"] += 1
                    out["today_allowed"] += d == today
                elif e.get("outcome") == "deny":
                    out["denied"] += 1
                    out["today_denied"] += d == today
            elif kind == "done":
                out["done"] += 1
                out["today_done"] += d == today
        # racha: dias seguidos con actividad hasta hoy (o hasta ayer, si hoy aun no hay nada)
        d = date.fromtimestamp(now)
        if d.isoformat() not in days:
            d -= timedelta(days=1)
        while d.isoformat() in days:
            out["streak"] += 1
            d -= timedelta(days=1)
        return out
