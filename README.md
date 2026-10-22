# Claude Tray

Icono en la bandeja de KDE para manejar tus sesiones de **Claude Code** sin volver a la terminal:

- **Aprobar o rechazar** solicitudes de permiso desde una notificación flotante, con el detalle del comando o del diff.
- **Ver en qué está cada sesión**: si está trabajando, te espera o terminó, la última herramienta, tu último mensaje y su respuesta.
- **Consumo en tiempo real** de las ventanas de 5 horas y 7 días del plan, con la hora de reinicio.
- **Mascota tamagotchi** (estilo Clawd): vive en el icono y en el panel, cambia de ánimo según tus sesiones y te habla. Tiene hambre, energía y cariño; se le da de comer, se juega con ella y se la acaricia; sube de nivel con tu trabajo y desbloquea accesorios.
- **Responder preguntas** con opciones (`AskUserQuestion`) desde la notificación o el panel, incluida «Otra respuesta».
- **Escribirle a una sesión** desde el panel (respuestas rápidas o texto libre), si corre en Konsole.
- **Consumo por día**: gráfico de 7 o 30 días con tus tokens, leído de los registros locales de Claude Code.
- **Ir a la terminal**: lleva al frente la pestaña exacta de Konsole donde corre la sesión.

Diseño de vidrio translúcido con desenfoque real y saturación (*vibrancy*) a través de los efectos Blur y Contrast de KWin.

## Cómo funciona

```
claude (terminal) ──hook PermissionRequest──▶ socket local ──▶ notificación  [Rechazar] [Permitir]
                  ◀─────────── allow / deny ─────────────────┘
                  ──hooks de estado (asíncronos)──▶ panel de sesiones
                  ──status line (rate_limits)─────▶ consumo 5 h / 7 d
~/.claude/sessions/<pid>.json ─────────────────▶ descubre las sesiones abiertas
```

- El socket vive en `$XDG_RUNTIME_DIR/claude-tray.sock`, accesible solo para tu usuario.
- **Si la app está cerrada**, el hook termina sin responder y Claude Code pregunta en la terminal como siempre.
- **Si no respondes** en `approval_timeout` segundos (por defecto 540), la pregunta vuelve a la terminal.
- **Si respondes en la terminal**, la notificación se cierra sola.
- Los comandos destructivos (`rm -rf`, `git push --force`, `sudo`, `git reset --hard`, …) piden **mantener presionado** «Permitir», y para ellos no se ofrece «Siempre».

## Instalación

Requiere KDE Plasma en X11 y [uv](https://docs.astral.sh/uv/). PySide6 6.12 necesita Python 3.12 o superior: con 3.10, Python termina cayéndose.

```bash
cd claude-tray
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python PySide6-Essentials
python3 install.py          # hooks + status line (con respaldo), lanzador, menú y autoarranque
claude-tray                 # o búscalo en el menú de aplicaciones
```

Las sesiones de Claude Code que ya estaban abiertas aparecen igual en el panel, pero los hooks nuevos se cargan recién al reiniciarlas.

Para desinstalar: `python3 install.py --uninstall` (deja tus otros hooks y ajustes como estaban).

## Uso

| Acción | Dónde |
|---|---|
| Abrir o cerrar el panel | clic en el icono de la bandeja (Esc cierra) |
| Permitir / Rechazar | botones de la notificación o del panel |
| Permitir siempre | «Siempre», que aplica la regla que sugiere Claude Code (p. ej. `Bash(git push:*)`) |
| Responder en la terminal | «Terminal», que devuelve la pregunta y te lleva a la pestaña |
| Responder una pregunta | elegir las opciones (o escribir «Otra respuesta») y «Responder»; «Terminal» la devuelve a la terminal |
| Escribirle a una sesión | clic en la sesión › respuestas rápidas o el campo «Escribir a esta sesión…» (solo Konsole) |
| Ver el consumo por día | clic en la tarjeta de consumo › 7 o 30 días; pasa el mouse por una barra para el detalle, o «Ver tabla» |
| Ver el historial | icono del reloj en el panel: lo aprobado, lo rechazado y lo que volvió a la terminal, con buscador y resumen del día |
| Ver detalle de una sesión | clic en la sesión, y luego «Ir a la terminal» |
| Avisos de «terminó» | menú contextual del icono, «Avisar cuando una sesión termine» |
| Dónde salen las notificaciones | selector «Esquina / Burbuja» al final del panel, o menú contextual › Notificaciones |

**Modo burbuja:** las notificaciones salen como globos de diálogo sobre el icono de la bandeja, con un pico que lo apunta. KDE no informa dónde está el icono, así que la app recuerda dónde hiciste clic en él: **haz clic una vez en el icono** para que el pico quede bien alineado. Mientras el panel está abierto, las burbujas se esconden, porque las solicitudes ya se ven en el panel.

**La mascota.** Clic en ella abre su ficha: nivel y experiencia, saciedad, energía y cariño, días de vida, aprobadas, tareas y racha, y los botones para darle comida (manzana, pizza o galleta), jugar y acariciarla.

| Ánimo | Cuándo | Cómo se ve |
|---|---|---|
| Te espera | hay una solicitud o pregunta | saluda con «!» (permiso), «?» (pregunta) o 💧 (comando destructivo) |
| Trabajando / pensando | una sesión trabaja / aún no usa herramientas | rebota y mira a los lados / globo «…» |
| Feliz / celebrando | terminó una tarea / una de más de 10 min | salta con ojos ^ ^ / confeti |
| Preocupada | una sesión se detuvo por un error | tiembla y suda |
| Con hambre / cansada | saciedad < 25 % / energía < 20 % o uso 5 h ≥ 80 % | piensa en una manzana / ojos caídos y se balancea |
| Aburrida / durmiendo | 45 min sin actividad / sin sesiones | mira de reojo / zZ |
| Comiendo, jugando, cariño | justo después de cada acción | mastica, da volteretas, corazones |

Experiencia: +10 por tarea (+25 si fue larga) y +2 por aprobación o comida. Accesorios: sombrero y moño desde el nivel 1, lentes desde el 2, audífonos desde el 3, flor desde el 4 y corona desde el 5. El ⚙ abre los ajustes (nombre, color, accesorio, notificaciones, icono). Si eliges el icono «Destello», este gira mientras alguna sesión trabaja y muestra un punto naranja cuando alguna te espera.

## Configuración

`~/.config/claude-tray/config.json`:

```json
{
  "approval_timeout": 540,
  "notify_done": true,
  "toast_position": "corner",
  "statusline_chain": null
}
```

`statusline_chain` guarda la status line que tenías antes de instalar: se sigue mostrando en la terminal y, además, se envían los datos de consumo a la app.

## Desarrollo

```bash
uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest          # 67 tests: estado, hook, historial, instalador…
```

```bash
.venv/bin/python -m claudetray --demo            # datos de ejemplo, panel fijo
.venv/bin/python -m claudetray --demo --bubble   # probar el modo burbuja (no se guarda)
.venv/bin/python -m claudetray --demo --history  # historial de ejemplo (en un archivo temporal)
.venv/bin/python -m claudetray --demo --pet      # ficha de la mascota (mascota temporal, nivel 3)
.venv/bin/python -m claudetray --demo --question # una pregunta con opciones
.venv/bin/python -m claudetray --demo --usage    # el gráfico de consumo por día
tools/e2e_ask.sh /ruta/salida                    # prueba real de AskUserQuestion con Claude Code (Konsole aparte)
tools/demo.sh                           # eventos de prueba a través del hook real
tools/shoot.sh /ruta/salida             # captura con un fondo de colores (sin tus ventanas)
```

Estructura:

- `hook/`: scripts que ejecuta Claude Code (solo stdlib, unos 20 ms).
- `claudetray/`: la app (PySide6 + QML).
  - `bridge.py`: socket local.
  - `state.py`: sesiones y consumo.
  - `pet.py`: la mascota tamagotchi (necesidades, nivel, acciones, ánimo y frases), sin Qt.
  - `usagehist.py`: tokens por día leídos de `~/.claude/projects/**/*.jsonl` (incremental, en segundo plano).
  - `history.py`: historial de decisiones y estadísticas (JSONL en `~/.local/share/claude-tray/`).
  - `describe.py`: resumen de cada herramienta y detección de comandos destructivos.
  - `glass.py`: desenfoque y *vibrancy* de KWin vía libX11.
  - `focus.py`: Konsole por DBus y `wmctrl`.
  - `workarea.py`: área útil real descontando los paneles (Qt la informa mal con varios monitores).
  - `qml/`: la interfaz.
