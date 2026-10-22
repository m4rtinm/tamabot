import json
import time

from tamabot import history
from tamabot.history import History


def noon(days_ago=0):
    t = time.localtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday - days_ago, 12, 0, 0, 0, 0, -1))


def test_guarda_y_recarga(tmp_path):
    h = History(tmp_path / "h.jsonl")
    h.add("decision", outcome="allow", project="web", title="Ejecutar comando")
    h.add("done", project="web")
    again = History(tmp_path / "h.jsonl")
    assert [e["kind"] for e in again.entries] == ["decision", "done"]
    assert again.recent(1)[0]["kind"] == "done"


def test_ignora_lineas_corruptas(tmp_path):
    p = tmp_path / "h.jsonl"
    p.write_text(json.dumps({"ts": 1, "kind": "done"}) + "\n{roto\n")
    assert len(History(p).entries) == 1


def test_recorta_al_maximo(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "MAX_ENTRIES", 10)
    h = History(tmp_path / "h.jsonl")
    for i in range(13):
        h.add("done", n=i)
    assert len(h.entries) == 10 and h.entries[0]["n"] == 3
    assert len((tmp_path / "h.jsonl").read_text().splitlines()) == 10


def test_estadisticas_y_racha(tmp_path):
    h = History(tmp_path / "h.jsonl")
    h.add("decision", ts=noon(), outcome="allow")
    h.add("decision", ts=noon(), outcome="always")
    h.add("decision", ts=noon(), outcome="deny")
    h.add("decision", ts=noon(), outcome="elsewhere")
    h.add("done", ts=noon())
    h.add("done", ts=noon(1))
    h.add("done", ts=noon(2))
    h.add("done", ts=noon(4))          # hueco: no cuenta para la racha
    st = h.stats(now=noon())
    assert (st["today_allowed"], st["today_denied"], st["today_done"]) == (2, 1, 1)
    assert (st["allowed"], st["denied"], st["done"]) == (2, 1, 4)
    assert st["streak"] == 3
    assert st["first"] == noon(4)


def test_racha_sigue_viva_si_hoy_aun_no_hay_actividad(tmp_path):
    h = History(tmp_path / "h.jsonl")
    h.add("done", ts=noon(1))
    h.add("done", ts=noon(2))
    assert h.stats(now=noon())["streak"] == 2


def test_recientes_ordenados_por_fecha(tmp_path):
    h = History(tmp_path / "h.jsonl")
    h.add("done", ts=noon(), n="hoy")
    h.add("done", ts=noon(3), n="antiguo")
    h.add("done", ts=noon(1), n="ayer")
    assert [e["n"] for e in h.recent()] == ["hoy", "ayer", "antiguo"]
