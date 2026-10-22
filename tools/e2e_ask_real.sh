#!/usr/bin/env bash
# Prueba con Traychi instalado: la pregunta debe verse en la terminal Y en Traychi; se contesta en la
# terminal (Enter enviado por DBus) y Traychi debe cerrar la notificación y registrarlo.
cd "$(dirname "$0")/.."
OUT=$1
WORK=$(mktemp -d "$HOME/.cache/traychi-e2e.XXXX")
HIST="$HOME/.local/share/traychi/history.jsonl"
before=$(wc -l < "$HIST")
konsole --separate --workdir "$PWD" -e claude --model haiku \
  "Usa la herramienta AskUserQuestion para preguntarme qué color prefiero, con las opciones exactamente Verde, Azul y Rojo (una sola respuesta). Después responde solo: ELEGISTE <color>." >/dev/null 2>&1 &
KP=$!
sleep 14                                                  # Claude piensa y hace la pregunta
import -window root "$OUT/ambos.png"                      # terminal + notificacion de Traychi a la vez
SVC="org.kde.konsole-$KP"
for s in $(qdbus "$SVC" | grep '^/Sessions/'); do qdbus "$SVC" "$s" sendText $'\r' >/dev/null; done
sleep 8
WID=$(wmctrl -lp | awk -v p=$KP '$3==p{print $1}' | head -1)
[ -n "$WID" ] && import -window "$WID" "$OUT/terminal-final.png"
import -window root "$OUT/despues.png"
kill $KP 2>/dev/null
rm -rf "$WORK"
echo "--- historial nuevo:"; tail -n +$((before + 1)) "$HIST"
