"""Servidor falso: responde las solicitudes de permiso con una decision fija y registra los eventos."""
import json, os, socket, sys
path, decision, log = sys.argv[1], sys.argv[2], open(sys.argv[3], "w")
if os.path.exists(path):
    os.unlink(path)
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); srv.bind(path); srv.listen(8)
while True:
    c, _ = srv.accept()
    buf = b""
    while b"\n" not in buf:
        chunk = c.recv(65536)
        if not chunk: break
        buf += chunk
    if not buf: c.close(); continue
    msg = json.loads(buf.split(b"\n")[0]); d = msg["data"]
    log.write(f'{msg["kind"]} {d.get("hook_event_name","status")} {d.get("tool_name","")} {json.dumps(d.get("tool_input",""), ensure_ascii=False)[:160]}\n')
    if d.get("hook_event_name") == "Stop":
        log.write(f'  respuesta final de Claude: {d.get("last_assistant_message","")[:200]}\n')
    log.flush()
    if msg["kind"] == "question":       # responde la primera opcion de cada pregunta
        qs = d.get("tool_input", {}).get("questions", [])
        answers = {q["question"]: q["options"][0]["label"] for q in qs}
        log.write(f"  respuestas: {answers}\n"); log.flush()
        c.sendall((json.dumps({"answers": answers}) + "\n").encode())
    elif msg["kind"] == "permission":
        dec = {"behavior": "allow"} if decision == "allow" else {"behavior": "deny", "message": "Rechazado desde la prueba"}
        c.sendall((json.dumps({"decision": dec}) + "\n").encode())
    c.close()
