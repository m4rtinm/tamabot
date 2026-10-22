#!/usr/bin/env python3
"""Puente entre los hooks de Claude Code y Claude Tray.

Con el argumento --ask (registrado como PreToolUse sincrono para AskUserQuestion)
espera a que respondas la pregunta en la app y se la entrega a Claude.

Solo usa la stdlib y arranca con `python3 -I -S` para que sea rapido.
Si la app no esta abierta (o no responde a tiempo) termina sin imprimir
nada, asi Claude Code sigue con su flujo normal y pregunta en la terminal.
"""
import json
import os
import socket
import sys
import uuid

RUNTIME = os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/claude-tray-{os.getuid()}"
SOCK = os.path.join(RUNTIME, "claude-tray.sock")
CONFIG = os.path.join(os.path.expanduser("~"), ".config", "claude-tray", "config.json")


def approval_timeout():
    try:
        with open(CONFIG) as f:
            return float(json.load(f).get("approval_timeout", 540))
    except Exception:
        return 540.0


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    event = data.get("hook_event_name", "")
    asking = "--ask" in sys.argv and event == "PreToolUse" and data.get("tool_name") == "AskUserQuestion"
    if "--ask" in sys.argv and not asking:
        return
    waiting = event == "PermissionRequest" or asking
    msg = {
        "kind": "question" if asking else "permission" if waiting else "event",
        "id": uuid.uuid4().hex,
        "ppid": os.getppid(),
        "data": data,
    }
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(SOCK)
        s.sendall((json.dumps(msg) + "\n").encode())
        if not waiting:
            s.close()
            return
        s.settimeout(approval_timeout())
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                return
            buf += chunk
        reply = json.loads(buf.split(b"\n", 1)[0])
    except (OSError, ValueError):
        return

    answers = reply.get("answers")
    if asking:
        if answers:
            # updatedInput reemplaza la entrada completa: se devuelven las preguntas + las respuestas
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": {**(data.get("tool_input") or {}), "answers": answers},
                }
            }))
        return
    decision = reply.get("decision")
    if decision:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": decision,
            }
        }))


if __name__ == "__main__":
    main()
