#!/usr/bin/env bash
# Envia eventos de prueba a Traychi a traves del hook real.
H="$(dirname "$0")/../hook/traychi_hook.py"
S=${1:-demo-session-1}
send() { printf '%s' "$1" | python3 -I -S "$H"; }
send '{"session_id":"'$S'","hook_event_name":"UserPromptSubmit","cwd":"'$HOME'/proyectos/webapp","prompt":"Arregla los tests que fallan en el módulo de pagos"}'
send '{"session_id":"'$S'","hook_event_name":"PreToolUse","cwd":"'$HOME'/proyectos/webapp","tool_name":"Bash","tool_input":{"command":"npm test -- payments"}}'
printf '%s' '{"session_id":"'$S'","prompt_id":"p1","hook_event_name":"StatusLine","model":{"display_name":"Opus 5.5"},"context_window":{"used_percentage":34},"cost":{"total_cost_usd":1.27},"rate_limits":{"five_hour":{"used_percentage":23.5,"resets_at":'$(( $(date +%s) + 7980 ))'},"seven_day":{"used_percentage":71.2,"resets_at":'$(( $(date +%s) + 300000 ))'}}}' | python3 -I -S "$(dirname "$0")/../hook/traychi_statusline.py" >/dev/null
send '{"session_id":"'$S'","hook_event_name":"PermissionRequest","cwd":"'$HOME'/proyectos/webapp","tool_name":"Bash","tool_input":{"command":"git push origin feature/pagos","description":"Sube la rama con el arreglo"},"permission_suggestions":[{"type":"addRules","rules":[{"toolName":"Bash","ruleContent":"git push:*"}],"behavior":"allow","destination":"localSettings"}]}'
