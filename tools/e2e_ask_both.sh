#!/usr/bin/env bash
# Prueba: ¿la pregunta (AskUserQuestion) se ve en la terminal mientras el hook PermissionRequest espera,
# y se puede responder desde el hook? Sesión interactiva real en un Konsole aparte.
cd "$(dirname "$0")/.."
OUT=$1
RUN=$(mktemp -d /tmp/ctr.XXXX)
H="/usr/bin/python3 -I -S $PWD/hook/traychi_hook.py"
cat > "$OUT/settings-both.json" <<JSON
{"hooks": {"PermissionRequest": [{"matcher": "*", "hooks": [{"type": "command", "command": "$H", "timeout": 600}]}]}}
JSON
: > "$OUT/log-both.txt"
python3 - "$RUN/traychi.sock" "$OUT/log-both.txt" <<'PY' &
import json, os, socket, sys, time
path, log = sys.argv[1], open(sys.argv[2], "w")
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); srv.bind(path); srv.listen(8)
while True:
    c, _ = srv.accept(); buf = b""
    while b"\n" not in buf:
        chunk = c.recv(65536)
        if not chunk: break
        buf += chunk
    if not buf: c.close(); continue
    msg = json.loads(buf.split(b"\n")[0]); d = msg["data"]
    log.write(f'{time.strftime("%X")} {msg["kind"]} {d.get("hook_event_name")} {d.get("tool_name","")}\n'); log.flush()
    if msg["kind"] == "permission" and d.get("tool_name") == "AskUserQuestion":
        time.sleep(10)                                   # tiempo para fotografiar la terminal
        qs = d["tool_input"]["questions"]
        answers = {q["question"]: q["options"][2]["label"] for q in qs}      # la tercera: no es la seleccionada por defecto
        log.write(f'{time.strftime("%X")}   responde: {answers}\n'); log.flush()
        try:
            c.sendall((json.dumps({"decision": {"behavior": "allow",
                       "updatedInput": {**d["tool_input"], "answers": answers}}}) + "\n").encode())
        except OSError as e:
            log.write(f"  (el hook ya se había cerrado: {e})\n")
    elif msg["kind"] == "permission":
        c.sendall(b'{"decision": null}\n')
    c.close()
PY
RP=$!
sleep 0.5
konsole --separate --workdir "$PWD" -p tabtitle=prueba-preguntas -e env XDG_RUNTIME_DIR="$RUN" claude --model haiku --setting-sources local \
  --settings "$OUT/settings-both.json" \
  "Usa la herramienta AskUserQuestion para preguntarme qué color prefiero, con las opciones exactamente Verde, Azul y Rojo (una sola respuesta). Después responde solo: ELEGISTE <color>." >/dev/null 2>&1 &
KP=$!
for i in $(seq 1 60); do grep -q "PermissionRequest AskUserQuestion" "$OUT/log-both.txt" && break; sleep 1; done
sleep 5
WID=$(wmctrl -lp | awk -v p=$KP '$3==p{print $1}' | head -1)
[ -n "$WID" ] && import -window "$WID" "$OUT/terminal-esperando.png"
sleep 12
[ -n "$WID" ] && import -window "$WID" "$OUT/terminal-despues.png"
kill $KP $RP 2>/dev/null
rm -rf "$RUN"
cat "$OUT/log-both.txt"
