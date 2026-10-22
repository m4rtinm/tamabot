"""Tokens por dia leidos de los registros locales de Claude Code (~/.claude/projects/**/*.jsonl).

Lectura incremental: se guarda hasta donde se leyo cada archivo, asi que tras la
primera pasada solo se procesa lo nuevo. Cada respuesta aparece repetida (una
linea por bloque de contenido) con el mismo id de mensaje: se cuenta una vez.
"""
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import CACHE_DIR

PROJECTS_DIR = Path.home() / ".claude" / "projects"
FIELDS = ("input", "output", "cache_write", "cache_read", "messages")
CACHE_VERSION = 1


def local_day(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().date().isoformat()
    except (ValueError, AttributeError):
        return None


class DailyUsage:
    def __init__(self, root=None, cache_path=None):
        self.root = Path(root) if root else PROJECTS_DIR
        self.cache_path = Path(cache_path) if cache_path else CACHE_DIR / "daily-usage.json"
        self.files = {}     # ruta -> {"offset": bytes leidos, "last": ultimo id de mensaje}
        self.days = {}      # "YYYY-MM-DD" -> {input, output, cache_write, cache_read, messages}
        self.updated = 0.0
        self._load()

    def _load(self):
        try:
            d = json.loads(self.cache_path.read_text())
            if d.get("v") == CACHE_VERSION:
                self.files, self.days, self.updated = d["files"], d["days"], d.get("updated", 0.0)
        except (OSError, ValueError, KeyError):
            pass

    def _save(self):
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps({"v": CACHE_VERSION, "files": self.files,
                                                   "days": self.days, "updated": self.updated}))
        except OSError:
            pass

    def refresh(self):
        """Lee lo nuevo de cada registro. Devuelve cuantos mensajes se agregaron."""
        try:
            paths = sorted(str(p) for p in self.root.rglob("*.jsonl"))
        except OSError:
            paths = []
        sizes = {}
        for p in paths:
            try:
                sizes[p] = Path(p).stat().st_size
            except OSError:
                pass
        # un registro que se achico o desaparecio invalida lo contado: se rehace todo
        if any(p not in sizes or sizes[p] < info["offset"] for p, info in self.files.items()):
            self.files, self.days = {}, {}
        added = 0
        for p, size in sizes.items():
            info = self.files.setdefault(p, {"offset": 0, "last": ""})
            if size > info["offset"]:
                added += self._read(p, info)
        self.updated = time.time()
        self._save()
        return added

    def _read(self, path, info):
        added = 0
        with open(path, "rb") as f:
            f.seek(info["offset"])
            for raw in f:
                if not raw.endswith(b"\n"):      # linea a medio escribir: se lee la proxima vez
                    break
                info["offset"] += len(raw)
                if b'"usage"' not in raw or b'"assistant"' not in raw:
                    continue
                try:
                    d = json.loads(raw)
                except ValueError:
                    continue
                msg = d.get("message") or {}
                usage = msg.get("usage")
                if d.get("type") != "assistant" or not usage:
                    continue
                mid = msg.get("id") or d.get("requestId") or ""
                if mid and mid == info["last"]:
                    continue
                info["last"] = mid
                day = local_day(d.get("timestamp", ""))
                if not day:
                    continue
                row = self.days.setdefault(day, dict.fromkeys(FIELDS, 0))
                row["input"] += usage.get("input_tokens") or 0
                row["output"] += usage.get("output_tokens") or 0
                row["cache_write"] += usage.get("cache_creation_input_tokens") or 0
                row["cache_read"] += usage.get("cache_read_input_tokens") or 0
                row["messages"] += 1
                added += 1
        return added

    def series(self, n, today=None):
        """Ultimos n dias (incluido hoy), con ceros donde no hubo uso."""
        today = today or date.today()
        out = []
        for i in range(n - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            row = dict(self.days.get(d) or dict.fromkeys(FIELDS, 0))
            row["date"] = d
            row["total"] = row["input"] + row["output"] + row["cache_write"]
            out.append(row)
        return out

    def summary(self, n, today=None):
        rows = self.series(n, today)
        totals = [r["total"] for r in rows]
        past = totals[:-1]
        active = [t for t in past if t > 0]
        avg = sum(active) / len(active) if active else 0
        peak = max(rows, key=lambda r: r["total"]) if rows else None
        return {
            "total": sum(totals), "today": totals[-1] if totals else 0,
            "avg": avg, "ratio": (totals[-1] / avg) if avg else 0,
            "peakDate": peak["date"] if peak and peak["total"] else "", "peak": peak["total"] if peak else 0,
            "activeDays": sum(1 for t in totals if t > 0),
        }
