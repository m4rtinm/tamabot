import pytest

from claudetray.pet import PetState, compute_mood, level_for, pet_line, xp_for_level

T0 = 1_800_000_000.0


@pytest.fixture
def pet(tmp_path):
    return PetState(tmp_path / "pet.json", now=T0)


def test_niveles():
    assert [level_for(x) for x in (0, 49, 50, 199, 200, 450)] == [1, 1, 2, 2, 3, 4]
    assert xp_for_level(level_for(260)) <= 260 < xp_for_level(level_for(260) + 1)


def test_el_tiempo_da_hambre_y_descansar_recupera_energia(pet):
    pet.d.update(hunger=80, energy=50, happy=70)
    pet.tick(T0 + 5 * 3600, sessions=0)
    assert pet.d["hunger"] == 60 and pet.d["happy"] == 60 and pet.d["energy"] == 100
    pet.tick(T0 + 7 * 3600, sessions=1, working=1)
    assert pet.d["energy"] == 92


def test_ausencia_larga_tiene_tope(pet):
    pet.tick(T0 + 30 * 86400)
    assert pet.d["hunger"] == 0 and pet.d["happy"] == 0       # 48 h maximo, pero ya basta para vaciar
    pet.d.update(hunger=100)
    pet.tick(T0 + 30 * 86400)                                 # mismo instante: no cambia
    assert pet.d["hunger"] == 100


def test_comer(pet):
    pet.d["hunger"] = 50
    ok, msg = pet.feed("pizza", T0)
    assert ok and pet.d["hunger"] == 90 and "pizza" in msg
    assert pet.active_transient(T0 + 1) == "eat" and pet.active_transient(T0 + 10) == ""
    pet.d["hunger"] = 96
    assert pet.feed("apple", T0)[0] is False
    assert pet.feed("sushi", T0)[0] is False


def test_jugar_cansa_y_no_se_puede_agotado(pet):
    ok, _ = pet.play(T0)
    assert ok and pet.d["energy"] == 80
    pet.d["energy"] = 10
    ok, msg = pet.play(T0)
    assert not ok and "cansado" in msg


def test_experiencia_y_desbloqueos(pet):
    assert "crown" not in pet.unlocked() and "hat" in pet.unlocked()
    for _ in range(80):
        pet.on_done(long_task=True)
    assert pet.level >= 5 and "crown" in pet.unlocked()


def test_se_guarda_y_se_recupera(tmp_path, pet):
    pet.feed("apple", T0)
    again = PetState(tmp_path / "pet.json", now=T0 + 99)
    assert again.d["xp"] == 2 and again.d["born"] == T0


def test_vista(pet):
    v = pet.view(T0 + 3 * 86400 + 5)
    assert v["ageDays"] == 3 and v["level"] == 1 and 0 <= v["progress"] < 1 and v["toNext"] == 50


# --- animo: el orden de prioridad importa ---------------------------------------
def mood(pet, **kw):
    return compute_mood(T0, pet, **kw)


def test_prioridades(pet):
    assert mood(pet) == ("sleep", "zz")
    assert mood(pet, sessions=1) == ("idle", "")
    assert mood(pet, sessions=1, working=1) == ("working", "")
    assert mood(pet, sessions=1, working=1, thinking_only=True) == ("thinking", "dots")
    assert mood(pet, sessions=1, pending=1) == ("waiting", "!")
    assert mood(pet, sessions=1, waiting=1) == ("waiting", "?")
    assert mood(pet, sessions=1, pending=1, danger=True) == ("waiting", "sweat")
    assert mood(pet, sessions=1, last_done=T0 - 10) == ("happy", "sparkle")
    assert mood(pet, sessions=1, last_done=T0 - 10, last_done_long=True) == ("celebrate", "confetti")
    assert mood(pet, sessions=1, last_done=T0 - 200) == ("idle", "")
    assert mood(pet, sessions=1, last_fail=T0 - 5) == ("worried", "sweat")
    assert mood(pet, sessions=1, last_event=T0 - 3600) == ("bored", "")
    assert mood(pet, sessions=1, usage_5h=85) == ("tired", "")


def test_necesidades_y_acciones_cambian_el_animo(pet):
    pet.d["hunger"] = 10
    assert mood(pet, sessions=1) == ("hungry", "food")
    assert mood(pet, sessions=1, pending=1)[0] == "waiting"       # avisar gana al hambre
    pet.d["hunger"], pet.d["energy"] = 80, 10
    assert mood(pet, sessions=1)[0] == "tired"
    pet.caress(T0)
    assert mood(pet, sessions=1, pending=1) == ("love", "heart")   # la accion recien hecha gana


def test_frases():
    # varias opciones por animo: se verifica el dato que llevan, no la frase exacta
    for t in range(0, 600, 20):
        assert "web" in pet_line("waiting", "!", T0 + t, pending=1, project="web")
        assert "3" in pet_line("waiting", "!", T0 + t, pending=3)
        assert "85 %" in pet_line("tired", "", T0 + t, usage_5h=85)
        assert "api" in pet_line("celebrate", "confetti", T0 + t, done_project="api")
    for m in ("idle", "working", "thinking", "hungry", "bored", "sleep", "worried", "happy"):
        assert pet_line(m, "", T0, project="x", done_project="y")


def test_frases_varian_pero_no_parpadean():
    vistas = {pet_line("working", "", T0 + t, project="web") for t in range(0, 1200, 20)}
    assert len(vistas) >= 4                                   # hay variedad
    assert pet_line("working", "", T0 + 1, project="web") == pet_line("working", "", T0 + 5, project="web")


def test_frases_con_datos_propios():
    vistas = {pet_line("idle", "", T0 + t, streak=5, level=4, name="Byte") for t in range(0, 4000, 20)}
    assert any("5 días" in v for v in vistas) and any("nivel 4" in v for v in vistas)
    assert any("Byte" in v for v in vistas)


def test_reacciones():
    from claudetray.pet import reaction
    assert reaction("prompt", T0, "api")
    assert "{p}" not in reaction("start", T0, "api")
    assert reaction("nada", T0) == ""
