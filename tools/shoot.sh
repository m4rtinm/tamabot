#!/usr/bin/env bash
# Captura de prueba: fondo de colores + app con el panel abierto + eventos de demo.
cd "$(dirname "$0")/.."
OUT=${1:-/tmp}
# solo se cierran las demos: tu Traychi real sigue abierto (la demo usa su propio socket)
pkill -f "tools/backdrop.py"; pkill -f "m traychi --demo"; sleep 0.5
DEMO_RT=$(mktemp -d); chmod 700 "$DEMO_RT"
timeout 25 .venv/bin/python tools/backdrop.py >/dev/null 2>&1 &
sleep 2
true
sleep 0.3
XDG_RUNTIME_DIR="$DEMO_RT" timeout 22 .venv/bin/python -m traychi --demo $ARGS > "$OUT/app.log" 2>&1 &
sleep 1
true
sleep ${DELAY:-2.5}
import -window root "$OUT/shot.png"
convert "$OUT/shot.png" -crop 560x1100+2000+460 "$OUT/panel.png"
convert "$OUT/shot.png" -crop 480x660+2080+0 "$OUT/toast.png"
convert "$OUT/shot.png" -crop 760x900+1800+700 "$OUT/bubble.png"
