"""Genera las ilustraciones vectoriales del README (docs/svg/*.svg).

Son maquetas simplificadas de la interfaz, para explicar cada función de un vistazo.
Uso: python3 tools/make_illustrations.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "svg"

BG, CARD, CARD2, STROKE = "#0E1726", "#172234", "#1E2B42", "#2C3D5A"
TEXT, MUTED, DIM = "#E9EEF5", "#93A3B8", "#5F6F86"
GREEN, GREEN_BTN, AMBER, RED, BLUE, ORANGE = "#3DD68C", "#26A96E", "#FF9F0A", "#FF5A52", "#64D2FF", "#D97757"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, t, size=14, color=TEXT, weight=400, anchor="start", mono=False, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{MONO if mono else FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}" {extra}>{esc(t)}</text>')


def rect(x, y, w, h, r=10, fill=CARD, stroke=STROKE, sw=1, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def button(x, y, w, label, kind="glass"):
    fill, color, stroke = {"accent": (GREEN_BTN, "#FFFFFF", GREEN_BTN), "danger": ("#3A1F25", "#FF8A84", "#5A2A32"),
                           "glass": ("#243450", TEXT, STROKE)}[kind]
    return rect(x, y, w, 30, 9, fill, stroke) + text(x + w / 2, y + 20, label, 13, color, 600, "middle")


def clawd(x, y, s=1.0, color=ORANGE):
    """El robotito Clawd (diseño por defecto)."""
    g = f'<g transform="translate({x},{y}) scale({s})">'
    for lx in (14, 24, 46, 56):
        g += f'<rect x="{lx}" y="52" width="6" height="12" rx="2" fill="#B9603F"/>'
    g += f'<rect x="2" y="30" width="10" height="11" rx="3" fill="{color}"/><rect x="68" y="30" width="10" height="11" rx="3" fill="{color}"/>'
    g += f'<rect x="9" y="17" width="62" height="38" rx="9" fill="{color}"/>'
    g += '<rect x="15" y="21" width="16" height="5" rx="2.5" fill="#FFFFFF" fill-opacity="0.25"/>'
    g += '<rect x="27" y="28" width="6" height="12" rx="3" fill="#2B1D17"/><rect x="47" y="28" width="6" height="12" rx="3" fill="#2B1D17"/>'
    return g + "</g>"


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title>'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#132036"/>'
            f'<stop offset="1" stop-color="{BG}"/></linearGradient>'
            f'<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{GREEN}"/></marker></defs>'
            f'<rect width="{w}" height="{h}" rx="18" fill="url(#bg)"/>{body}</svg>\n')


def notification(x, y, w, project, title, cmd, buttons=True, danger=False):
    b = rect(x, y, w, 168 if buttons else 120, 16, CARD2)
    b += clawd(x + 14, y + 10, 0.24) + text(x + 38, y + 24, f"CLAUDE CODE  ·  {project}", 11, MUTED, 700, extra='letter-spacing="0.6"')
    b += text(x + w - 14, y + 24, "ahora", 11, DIM, 400, "end")
    b += text(x + 16, y + 52, title, 15, TEXT, 700)
    if danger:
        b += rect(x + 150, y + 38, 82, 20, 6, "#3A1F25", "#3A1F25") + text(x + 191, y + 52, "Destructivo", 11, "#FF8A84", 700, "middle")
    b += rect(x + 16, y + 64, w - 32, 34, 9, "#0B1220") + text(x + 28, y + 86, cmd, 13, TEXT, 400, mono=True)
    if buttons:
        if w >= 380:                       # en las tarjetas angostas no caben los dos enlaces
            b += text(x + 18, y + 135, "Siempre", 13, MUTED) + text(x + 86, y + 135, "Terminal", 13, MUTED)
        else:
            b += text(x + 18, y + 135, "Terminal", 13, MUTED)
        if danger:
            b += button(x + w - 228, y + 116, 96, "Rechazar") + rect(x + w - 124, y + 116, 108, 30, 9, "#3A1F25", "#5A2A32")
            b += rect(x + w - 124, y + 116, 62, 30, 9, RED, RED) + text(x + w - 70, y + 136, "Mantén", 13, "#FFFFFF", 700, "middle")
        else:
            b += button(x + w - 206, y + 116, 96, "Rechazar") + button(x + w - 102, y + 116, 86, "Permitir", "accent")
    return b


def como_funciona():
    b = ""
    # terminal
    b += rect(24, 44, 290, 196, 14, "#0B1220")
    b += "".join(f'<circle cx="{44 + i * 16}" cy="62" r="5" fill="{c}"/>' for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")))
    b += text(120, 66, "terminal", 12, DIM, 400)
    b += text(44, 100, "$", 14, GREEN, 700, mono=True) + text(60, 100, "claude", 14, TEXT, 400, mono=True)
    b += text(44, 128, "› sube la rama a GitHub", 13, MUTED, mono=True)
    b += text(44, 160, "● necesita permiso:", 13, AMBER, mono=True)
    b += text(60, 184, "git push origin main", 13, TEXT, mono=True)
    b += text(44, 214, "esperando…", 13, DIM, mono=True)
    # flecha al hook y Traychi
    b += f'<path d="M 322 140 L 404 140" stroke="{GREEN}" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>'
    b += text(363, 128, "hook", 12, GREEN, 600, "middle")
    b += f'<circle cx="460" cy="140" r="50" fill="{CARD2}" stroke="{GREEN}" stroke-width="2"/>' + clawd(428, 104, 0.8)
    b += text(460, 214, "Traychi", 15, TEXT, 700, "middle") + text(460, 232, "en la bandeja", 12, MUTED, 400, "middle")
    b += f'<path d="M 516 140 L 596 140" stroke="{GREEN}" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>'
    # notificacion
    b += notification(604, 52, 330, "webapp", "Ejecutar comando", "git push origin main")
    # vuelta
    b += (f'<path d="M 840 226 C 840 300, 170 300, 170 248" stroke="{GREEN}" stroke-width="2.5" fill="none" '
          f'stroke-dasharray="6 6" marker-end="url(#arrow)"/>')
    b += text(505, 296, "tu decisión vuelve a Claude Code, que sigue trabajando", 13, GREEN, 600, "middle")
    b += text(480, 330, "Si Traychi está cerrado o no respondes a tiempo, Claude pregunta en la terminal como siempre.",
              12, MUTED, 400, "middle")
    return svg(960, 350, b, "Cómo funciona Traychi: Claude Code pide permiso, Traychi lo muestra y tu decisión vuelve a Claude")


def permisos():
    b = notification(24, 22, 400, "webapp", "Ejecutar comando", "git push origin feature/pagos")
    b += notification(64, 168, 400, "api", "Ejecutar comando", "rm -rf build/ dist/", danger=True)
    b += text(244, 362, "Los comandos destructivos piden mantener presionado", 12, MUTED, 400, "middle")
    return svg(488, 380, b, "Notificaciones de permiso con el comando a la vista")


def preguntas():
    b = rect(24, 22, 440, 330, 16, CARD2)
    b += clawd(38, 32, 0.24) + text(62, 46, "CLAUDE CODE  ·  webapp", 11, MUTED, 700, extra='letter-spacing="0.6"')
    b += rect(40, 60, 46, 20, 6, "#243450", "#243450") + text(63, 74, "Tests", 11, MUTED, 600, "middle")
    b += text(96, 74, "Puedes elegir varias", 11, DIM)
    b += text(40, 104, "¿Qué pruebas agrego?", 16, TEXT, 700)
    for i, (label, on) in enumerate((("Unitarias", True), ("Integración", True), ("E2E", False))):
        y = 118 + i * 44
        b += rect(40, y, 408, 36, 10, "#1F3A33" if on else CARD, "#2F7A5C" if on else STROKE)
        b += rect(52, y + 10, 16, 16, 4, GREEN_BTN if on else "none", GREEN_BTN if on else MUTED, 1.5)
        if on:
            b += f'<path d="M 55 {y + 18} l 3.5 3.5 l 6.5 -7" stroke="#FFFFFF" stroke-width="2" fill="none" stroke-linecap="round"/>'
        b += text(80, y + 23, label, 14, TEXT, 500)
    b += rect(40, 252, 408, 34, 10, "#0B1220") + text(54, 274, "Otra respuesta…", 13, DIM)
    b += text(42, 324, "Terminal", 13, MUTED) + button(352, 304, 96, "Responder", "accent")
    return svg(488, 376, b, "Responder las preguntas con opciones de Claude")


def sesiones():
    b = rect(24, 22, 440, 330, 16, CARD2)
    b += text(44, 54, "SESIONES", 12, MUTED, 700, extra='letter-spacing="0.8"')
    rows = [(BLUE, "webapp", "$ npm test -- payments", "ahora", "Opus 5.5 · contexto 34 %"),
            (AMBER, "api-gateway", "Necesita permiso · git push", "ahora", "Sonnet 5.5 · contexto 61 %"),
            (GREEN, "landing", "Terminado", "hace 2 min", "Opus 5.5 · contexto 82 %")]
    for i, (dot, name, act, when, meta) in enumerate(rows):
        y = 70 + i * 88
        b += rect(40, y, 408, 76, 12, CARD, "#6B4A1A" if dot == AMBER else STROKE)
        b += f'<circle cx="58" cy="{y + 22}" r="5" fill="{dot}"/>'
        if dot != GREEN:
            b += f'<circle cx="58" cy="{y + 22}" r="10" fill="{dot}" fill-opacity="0.18"/>'
        b += text(72, y + 27, name, 15, TEXT, 700) + text(432, y + 27, when, 11, DIM, 400, "end")
        b += text(72, y + 48, act, 13, AMBER if dot == AMBER else MUTED, 400, mono=act.startswith("$"))
        b += text(72, y + 66, meta, 11, DIM)
    b += text(244, 344, "Clic en una sesión: ir a su terminal o escribirle", 12, MUTED, 400, "middle")
    return svg(488, 370, b, "Todas tus sesiones de Claude Code y en qué está cada una")


def consumo():
    b = rect(24, 22, 440, 330, 16, CARD2)
    for i, (label, pct, color, reset) in enumerate((("Sesión (5 h)", 24, GREEN, "se reinicia en 2 h 12 min"),
                                                     ("Semana (7 d)", 71, AMBER, "se reinicia el vie 06:00"))):
        y = 50 + i * 62
        b += text(44, y, label, 14, TEXT, 500) + text(444, y, f"{pct} %", 14, color if pct >= 70 else TEXT, 700, "end")
        b += rect(44, y + 10, 400, 7, 3.5, "#243450", "none", 0) + rect(44, y + 10, 4 * pct, 7, 3.5, color, "none", 0)
        b += text(44, y + 34, reset, 11, DIM)
    b += text(44, 196, "Tokens por día", 12, MUTED)
    vals = [1.6, 0.4, 1.5, 0.2, 0.0, 2.3, 1.9]
    days = ["mié", "jue", "vie", "sáb", "dom", "lun", "hoy"]
    for i, v in enumerate(vals):
        x = 60 + i * 56
        h = v / 2.5 * 96
        b += f'<rect x="{x}" y="{306 - h}" width="38" height="{h + 4}" rx="4" fill="{GREEN_BTN}" fill-opacity="{1 if i == 6 else 0.7}"/>'
        b += text(x + 19, 324, days[i], 11, MUTED if i == 6 else DIM, 600 if i == 6 else 400, "middle")
    b += f'<line x1="44" y1="306" x2="444" y2="306" stroke="{STROKE}"/>'
    return svg(488, 370, b, "Consumo del plan en tiempo real y tokens por día")


def atajos():
    def key(x, y, label, w=None):
        w = w or max(44, 14 + 9 * len(label))
        return (rect(x, y + 4, w, 40, 8, "#0B1220", "#0B1220") + rect(x, y, w, 40, 8, "#243450", STROKE)
                + text(x + w / 2, y + 26, label, 14, TEXT, 600, "middle")), w
    b = ""
    for i, (k, what, color) in enumerate((("A", "Permitir la última", GREEN), ("D", "Rechazar la última", RED),
                                          ("C", "Abrir el panel", BLUE))):
        y = 36 + i * 74
        x = 40
        for label in ("Super", "Shift", k):
            kb, w = key(x, y, label)
            b += kb
            x += w + (24 if label != k else 0)
            if label != k:
                b += text(x - 12, y + 27, "+", 16, DIM, 600, "middle")
        b += f'<path d="M {x + 14} {y + 20} L {x + 46} {y + 20}" stroke="{color}" stroke-width="2.5" marker-end="url(#arrow)"/>'
        b += text(x + 58, y + 26, what, 15, TEXT, 600)
    b += text(244, 266, "En Wayland: traychi --allow · --deny · --panel", 12, MUTED, 400, "middle", mono=True)
    b += text(244, 288, "«Permitir» por atajo nunca aprueba comandos destructivos", 12, DIM, 400, "middle")
    return svg(488, 310, b, "Atajos de teclado para responder sin el mouse")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("como-funciona", como_funciona), ("permisos", permisos), ("preguntas", preguntas),
                     ("sesiones", sesiones), ("consumo", consumo), ("atajos", atajos)):
        (OUT / f"{name}.svg").write_text(fn())
        print(name)
