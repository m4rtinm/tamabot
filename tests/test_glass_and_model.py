import math
import struct

from claudetray.glass import color_matrix, rounded_region, tail_region
from claudetray.listmodel import DictListModel


def area(rects):
    return sum(w * h for _, _, w, h in rects)


def test_region_redondeada_dentro_de_limites_y_con_area_correcta():
    x, y, w, h, r = 22, 22, 372, 214, 22
    rects = rounded_region(x, y, w, h, r)
    for rx, ry, rw, rh in rects:
        assert rx >= x and ry >= y and rx + rw <= x + w and ry + rh <= y + h
    esperada = w * h - (4 - math.pi) * r * r
    assert abs(area(rects) - esperada) < 0.02 * esperada
    assert len(rects) * 4 > 64          # mas de lo que acepta xprop: por eso se usa libX11


def test_radio_mayor_que_la_mitad_se_limita():
    rects = rounded_region(0, 0, 20, 10, 50)
    assert all(rw >= 0 and rh >= 0 for _, _, rw, rh in rects)


def test_pico_de_burbuja_bajo_la_tarjeta():
    rects = tail_region(0, 0, 300, 100, 150, 10, 1)
    assert rects and all(ry >= 100 for _, ry, _, _ in rects)
    up = tail_region(0, 20, 300, 100, 150, 10, -1)
    assert all(ry + rh <= 20 for _, ry, _, rh in up)


def test_matriz_de_color_neutra_es_identidad():
    floats = [struct.unpack("f", struct.pack("I", v))[0] for v in color_matrix(1.0, 1.0, 1.0)]
    identidad = [1.0 if i % 5 == 0 else 0.0 for i in range(16)]
    assert all(abs(a - b) < 1e-6 for a, b in zip(floats, identidad))


def test_list_model_sync_inserta_mueve_actualiza_y_borra(qapp):
    m = DictListModel("k", ["k", "v"])
    m.sync([{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}])
    assert m.count == 3
    m.sync([{"k": "c", "v": 30}, {"k": "a", "v": 1}])
    assert [(i["k"], i["v"]) for i in m.items()] == [("c", 30), ("a", 1)]
    roles = {bytes(n).decode(): r for r, n in m.roleNames().items()}
    assert m.data(m.index(0), roles["v"]) == 30
