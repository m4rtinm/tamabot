#!/usr/bin/env bash
# Prueba real de AskUserQuestion: sesion interactiva de Claude Code en un Konsole aparte,
# con los hooks apuntando a un servidor falso que responde la primera opcion.
cd "$(dirname "$0")/.."
OUT=$1
RUN=$(mktemp -d /tmp/ctr.XXXX)
H="/usr/bin/python3 -I -S $PWD/hook/traychi_hook.py"
cat > "$OUT/settings-ask.json" <<JSON
{"hooks": {"PreToolUse": [{"matcher": "AskUserQuestion", "hooks": [{"type": "command", "command": "$H --ask", "timeout": 600}]}]}}
JSON
: > "$OUT/log-ask.txt"
python3 tools/e2e_responder.py "$RUN/traychi.sock" allow "$OUT/log-ask.txt" &
RP=$!
sleep 0.5
konsole --separate --workdir "$PWD" -e env XDG_RUNTIME_DIR="$RUN" claude --model haiku --settings "$OUT/settings-ask.json" \
  "Usa la herramienta AskUserQuestion para preguntarme qué color prefiero, con las opciones exactamente Verde, Azul y Rojo (una sola respuesta). Después responde solo: ELEGISTE <color>." >/dev/null 2>&1 &
KP=$!
for i in $(seq 1 90); do grep -q "respuesta final" "$OUT/log-ask.txt" && break; sleep 1; done
kill $KP $RP 2>/dev/null
rm -rf "$RUN"
cat "$OUT/log-ask.txt"
