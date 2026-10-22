"""La mascota como tamagotchi: necesidades, experiencia, acciones, animo y frases.

Python puro (sin Qt) para poder probarlo. Las necesidades van de 0 a 100,
donde 100 es lo mejor (saciado, descansado, feliz).
"""
import json
import math
import random
import time
from pathlib import Path

from .config import CONFIG_DIR

# comida: (saciedad, cariño, nombre)
FOODS = {
    "apple": (25, 3, "manzana"),
    "pizza": (40, 6, "pizza"),
    "cookie": (15, 10, "galleta"),
}
# accesorio: nivel necesario
UNLOCKS = {"": 1, "hat": 1, "bow": 1, "glasses": 2, "headphones": 3, "flower": 4, "crown": 5}
# los accesorios antiguos eran emojis
LEGACY_ACCESSORIES = {"🎩": "hat", "👑": "crown", "🎀": "bow", "🕶️": "glasses", "🎧": "headphones", "🌸": "flower"}

TRANSIENT_SECONDS = {"eat": 2.4, "play": 2.4, "love": 2.6}
MAX_CATCHUP_HOURS = 48     # si la app estuvo cerrada, no castigar mas que esto


def clamp(v):
    return max(0.0, min(100.0, v))


def level_for(xp):
    return 1 + int(math.sqrt(max(0, xp) / 50))


def xp_for_level(level):
    """XP acumulada necesaria para llegar a `level`."""
    return 50 * (level - 1) ** 2


class PetState:
    def __init__(self, path=None, now=None):
        self.path = Path(path) if path else CONFIG_DIR / "pet-state.json"
        now = now if now is not None else time.time()
        self.d = {"born": now, "hunger": 80.0, "energy": 90.0, "happy": 70.0, "xp": 0, "updated": now}
        try:
            self.d.update(json.loads(self.path.read_text()))
        except (OSError, ValueError):
            pass
        self.transient = ("", 0.0)      # (accion, hasta cuando)
        self._saved_at = 0.0

    # --- persistencia -----------------------------------------------------------
    def save(self, now=None):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.d))
            self._saved_at = now if now is not None else time.time()
        except OSError:
            pass

    def maybe_save(self, now):
        if now - self._saved_at > 60:
            self.save(now)

    # --- paso del tiempo ----------------------------------------------------------
    def tick(self, now, sessions=0, working=0):
        """Hambre y cariño bajan con el tiempo; la energia baja trabajando y sube descansando."""
        hours = min(MAX_CATCHUP_HOURS, max(0.0, (now - self.d["updated"]) / 3600))
        self.d["updated"] = now
        if not hours:
            return
        self.d["hunger"] = clamp(self.d["hunger"] - 4 * hours)
        self.d["happy"] = clamp(self.d["happy"] - 2 * hours)
        if working:
            self.d["energy"] = clamp(self.d["energy"] - 4 * hours)
        elif sessions == 0:
            self.d["energy"] = clamp(self.d["energy"] + 10 * hours)    # duerme y recupera
        else:
            self.d["energy"] = clamp(self.d["energy"] - 1 * hours)

    def _start(self, kind, now):
        self.transient = (kind, now + TRANSIENT_SECONDS[kind])

    def active_transient(self, now):
        kind, until = self.transient
        return kind if kind and now < until else ""

    # --- acciones del usuario ------------------------------------------------------
    def feed(self, food, now):
        if food not in FOODS:
            return False, "No conozco esa comida."
        if self.d["hunger"] >= 95:
            return False, "¡Estoy lleno! Gracias igual."
        full, love, name = FOODS[food]
        self.d["hunger"] = clamp(self.d["hunger"] + full)
        self.d["happy"] = clamp(self.d["happy"] + love)
        self.d["xp"] += 2
        self._start("eat", now)
        self.save(now)
        return True, f"¡Ñam! Gracias por la {name}."

    def play(self, now):
        if self.d["energy"] < 15:
            return False, "Estoy muy cansado para jugar… mejor después."
        if self.d["hunger"] < 10:
            return False, "Tengo demasiada hambre para jugar."
        self.d["happy"] = clamp(self.d["happy"] + 20)
        self.d["energy"] = clamp(self.d["energy"] - 10)
        self.d["hunger"] = clamp(self.d["hunger"] - 5)
        self.d["xp"] += 3
        self._start("play", now)
        self.save(now)
        return True, "¡Wiii! ¡Otra vez!"

    def caress(self, now):
        self.d["happy"] = clamp(self.d["happy"] + 8)
        self._start("love", now)
        self.save(now)
        phrases = ("Jeje, me haces cosquillas.", "¡Me encanta!", "Eres el mejor humano.")
        return True, phrases[int(now) % len(phrases)]

    # --- eventos de las sesiones -----------------------------------------------------
    def on_done(self, long_task=False):
        self.d["xp"] += 25 if long_task else 10
        self.d["energy"] = clamp(self.d["energy"] - 3)

    def on_approval(self):
        self.d["xp"] += 2

    # --- vista para QML -----------------------------------------------------------------
    @property
    def level(self):
        return level_for(self.d["xp"])

    def unlocked(self):
        return [a for a, lvl in UNLOCKS.items() if self.level >= lvl]

    def view(self, now):
        lvl = self.level
        lo, hi = xp_for_level(lvl), xp_for_level(lvl + 1)
        return {
            "hunger": round(self.d["hunger"]), "energy": round(self.d["energy"]), "happy": round(self.d["happy"]),
            "xp": self.d["xp"], "level": lvl, "progress": (self.d["xp"] - lo) / (hi - lo),
            "toNext": hi - self.d["xp"], "ageDays": int((now - self.d["born"]) // 86400),
            "unlocked": self.unlocked(), "unlocks": dict(UNLOCKS),
        }


def compute_mood(now, pet, *, sessions=0, working=0, thinking_only=False, waiting=0, pending=0,
                 danger=False, last_done=0.0, last_done_long=False, last_fail=0.0,
                 last_event=0.0, usage_5h=-1):
    """Devuelve (animo, emote). El orden marca la prioridad."""
    t = pet.active_transient(now)
    if t == "eat":
        return "eat", "food"
    if t == "play":
        return "play", "sparkle"
    if t == "love":
        return "love", "heart"
    if waiting or pending:
        return "waiting", "sweat" if danger else ("!" if pending else "?")
    if now - last_fail < 60:
        return "worried", "sweat"
    if working:
        return ("thinking", "dots") if thinking_only else ("working", "")
    if now - last_done < 90:
        return ("celebrate", "confetti") if last_done_long else ("happy", "sparkle")
    if pet.d["hunger"] < 25:
        return "hungry", "food"
    if pet.d["energy"] < 20 or usage_5h >= 80:
        return "tired", ""
    if sessions == 0:
        return "sleep", "zz"
    if last_event and now - last_event > 45 * 60:
        return "bored", ""
    return "idle", ""


def _pick(options, now, period=20):
    """Elige una frase al azar, estable durante `period` segundos (asi no parpadea al refrescar)."""
    options = [o for o in options if o]
    return random.Random(int(now // period) * 7919 + len(options)).choice(options) if options else ""


def _daypart(now):
    h = time.localtime(now).tm_hour
    return "morning" if 6 <= h < 12 else "afternoon" if 12 <= h < 20 else "night"


def pet_line(mood, emote, now, *, pending=0, project="", done_project="", working_n=0, usage_5h=-1,
             streak=0, level=1, hunger=100, energy=100, name="Clawd"):
    """Lo que dice la mascota: frases variadas segun el animo, la hora y tus datos."""
    p, dp = project or "la sesión", done_project or "la sesión"
    part = _daypart(now)
    if mood == "waiting":
        if pending > 1:
            return _pick([f"¡Hay {pending} solicitudes esperándote!", f"Tengo {pending} cosas para que revises.",
                          f"¡Psst! {pending} solicitudes en la fila."], now)
        if emote == "sweat":
            return _pick([f"Ojo: {p} quiere hacer algo delicado…", f"Mmm… lo que pide {p} es delicado. Revísalo bien.",
                          f"Esto de {p} puede borrar cosas. ¿Seguro?"], now)
        if pending:
            return _pick([f"¡{p} necesita tu permiso!", f"{p} quiere hacer algo. ¿Le das permiso?",
                          f"¡Eh! {p} está esperando tu visto bueno.", f"Necesito tu OK para seguir en {p}."], now)
        return _pick([f"{p} tiene una pregunta para ti.", f"¿Me ayudas? {p} quiere saber algo.",
                      f"Hay una pregunta esperándote en {p}."], now)
    if mood == "worried":
        return _pick(["Uy… una sesión se detuvo por un error.", "Algo falló. ¿Le echas un ojo?",
                      "Oh no, se cayó algo. Revisa la terminal."], now)
    if mood == "thinking":
        return _pick(["Hmm… pensando…", f"{p} está pensando…", "Dame un segundo, estoy pensando.",
                      "Pensando en la mejor forma de hacerlo…"], now)
    if mood == "working":
        if working_n > 1:
            return _pick([f"Cuidando {working_n} sesiones a la vez…", f"¡{working_n} sesiones trabajando! Qué ritmo.",
                          f"Malabareando {working_n} sesiones…"], now)
        return _pick([f"Trabajando en {p}…", f"Manos a la obra en {p}.", f"{p} va avanzando.",
                      "Tecleando a toda velocidad…", f"Concentrado en {p}.", "Esto va bien, sigo."], now)
    if mood == "celebrate":
        return _pick([f"¡Terminamos una tarea grande en {dp}!", f"¡Lo logramos! {dp} terminó un trabajo largo.",
                      f"¡Eso fue un maratón en {dp}! Tarea grande lista."], now)
    if mood == "happy":
        return _pick([f"¡Listo! {dp} terminó.", f"¡{dp} terminó! ¿Qué sigue?", f"Tarea completada en {dp}.",
                      f"¡Hecho! {dp} te espera para lo siguiente."], now)
    if mood == "hungry":
        return _pick(["Tengo hambre… ¿me das algo?", "Mi pancita suena…", "¿Una galletita? ¿Porfa?",
                      "Se me antojó una pizza…"], now)
    if mood == "tired":
        if usage_5h >= 80:
            return _pick([f"Uf, llevamos {round(usage_5h)} % del uso de 5 h…",
                          f"Vamos en {round(usage_5h)} % de la ventana de 5 h. Con calma."], now)
        return _pick(["Estoy cansado…", "Necesito una siesta.", "Bostezo… mucho trabajo hoy."], now)
    if mood == "sleep":
        if part == "night":
            return _pick(["Zzz… buenas noches.", "Zzz… ya es tarde, ¿no?", "Zzz… soñando con código limpio."], now)
        return _pick(["Zzz… no hay sesiones abiertas.", "Zzz… despiértame cuando abras claude.",
                      "Zzz… descansando un rato."], now)
    if mood == "bored":
        return _pick(["Qué aburrido… ¿jugamos?", "¿Hacemos algo?", "Llevo rato sin nada que hacer…",
                      "¿Y si me das de comer mientras?"], now)
    if mood in ("eat", "play", "love"):
        return ""
    # tranquilo: saludo segun la hora y comentarios sobre tus datos
    greet = {"morning": ["¡Buenos días!", "¡Buen día! ¿Qué hacemos hoy?", "Café y código, ¿no?"],
             "afternoon": ["¡Buenas tardes!", "Tarde productiva, ¿eh?", "¿Cómo va la tarde?"],
             "night": ["Buenas noches. ¿Aún trabajando?", "Ya es de noche… no te trasnoches.",
                       "Turno nocturno, ¿eh?"]}[part]
    extras = ["Todo tranquilo por aquí.", "Aquí estoy, vigilando.", f"{name} reportándose. Todo en orden.",
              "Sin novedades en el frente.", "Si necesitas algo, aquí estoy."]
    if streak >= 3:
        extras.append(f"¡Llevamos {streak} días seguidos trabajando juntos!")
    if level >= 2:
        extras.append(f"Ya voy en el nivel {level}. ¡Gracias por cuidarme!")
    if hunger < 50:
        extras.append("No me vendría mal un bocadillo…")
    if energy > 85:
        extras.append("¡Tengo energía de sobra!")
    return _pick(greet + extras, now)


REACTIONS = {
    "allow": ["¡Gracias! Sigo.", "¡Vamos!", "Perfecto, continúo.", "¡Dale!"],
    "always": ["¡Anotado! No te vuelvo a preguntar eso.", "Listo, para la próxima ya sé."],
    "deny": ["Entendido, no lo hago.", "Ok, lo dejo.", "Vale, buscaré otra forma."],
    "answered": ["¡Anotado, gracias!", "¡Perfecto, eso necesitaba!"],
    "prompt": ["¡Manos a la obra!", "¡Vamos con eso en {p}!", "Ok, a trabajar en {p}.", "¡Entendido! Empiezo en {p}."],
    "start": ["¡Hola! Se abrió una sesión en {p}.", "¡Nueva sesión en {p}!", "¡{p} se unió al equipo!"],
    "message": ["¡Mensaje enviado a {p}!", "Listo, se lo dije a {p}."],
}


def reaction(kind, now, project=""):
    return _pick(REACTIONS.get(kind, []), now, period=1).replace("{p}", project or "la sesión")
