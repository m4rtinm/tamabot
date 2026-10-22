import json
from datetime import date, datetime, timedelta, timezone

from claudetray.usagehist import DailyUsage


def line(day, mid, inp=10, out=5, cw=100, cr=1000, kind="assistant"):
    ts = datetime(day.year, day.month, day.day, 12, tzinfo=timezone.utc).astimezone(timezone.utc)
    return json.dumps({"type": kind, "timestamp": ts.isoformat().replace("+00:00", "Z"), "requestId": "r" + mid,
                       "message": {"id": mid, "usage": {"input_tokens": inp, "output_tokens": out,
                                                         "cache_creation_input_tokens": cw,
                                                         "cache_read_input_tokens": cr}}}) + "\n"


def setup(tmp_path):
    root = tmp_path / "projects" / "-p"
    root.mkdir(parents=True)
    return root, DailyUsage(root=tmp_path / "projects", cache_path=tmp_path / "cache.json")


def test_cuenta_cada_respuesta_una_vez(tmp_path):
    root, du = setup(tmp_path)
    today = date.today()
    (root / "a.jsonl").write_text(line(today, "m1") + line(today, "m1") + line(today, "m2")
                                  + json.dumps({"type": "user", "message": {"content": "hola"}}) + "\n")
    assert du.refresh() == 2
    row = du.series(1)[0]
    assert (row["input"], row["output"], row["cache_write"], row["cache_read"], row["messages"]) == (20, 10, 200, 2000, 2)
    assert row["total"] == 230                      # entrada + salida + cache escrita


def test_lectura_incremental_y_linea_a_medias(tmp_path):
    root, du = setup(tmp_path)
    today = date.today()
    f = root / "a.jsonl"
    full = line(today, "m2")
    f.write_text(line(today, "m1") + full[:30])      # la segunda linea aun se esta escribiendo
    assert du.refresh() == 1
    with f.open("a") as fh:
        fh.write(full[30:])
    assert du.refresh() == 1
    assert DailyUsage(root=tmp_path / "projects", cache_path=tmp_path / "cache.json").refresh() == 0   # cache persistido


def test_archivo_que_se_achica_rehace_la_cuenta(tmp_path):
    root, du = setup(tmp_path)
    today = date.today()
    f = root / "a.jsonl"
    f.write_text(line(today, "m1") + line(today, "m2"))
    du.refresh()
    f.write_text(line(today, "m9"))
    du.refresh()
    assert du.series(1)[0]["messages"] == 1


def test_serie_con_ceros_y_resumen(tmp_path):
    root, du = setup(tmp_path)
    today = date.today()
    (root / "a.jsonl").write_text(line(today - timedelta(days=2), "a", cw=0, cr=0, inp=100, out=100)
                                  + line(today, "b", cw=0, cr=0, inp=300, out=300))
    du.refresh()
    rows = du.series(7)
    assert len(rows) == 7 and rows[-1]["date"] == today.isoformat()
    assert [r["total"] for r in rows[-3:]] == [200, 0, 600]
    s = du.summary(7)
    assert s["total"] == 800 and s["avg"] == 200 and s["ratio"] == 3 and s["peak"] == 600
