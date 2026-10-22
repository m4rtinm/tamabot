"""Convierte la entrada de una herramienta en texto legible para la notificacion."""
import json
import os
import re

DANGER = [
    r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+",
    r"\bgit\s+push\b.*(--force\b|\s-f\b|--force-with-lease)",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[a-zA-Z]*f",
    r"\bgit\s+branch\s+-D\b",
    r"\bsudo\b",
    r"\bdd\s+if=",
    r"\bmkfs(\.\w+)?\b",
    r"\bchmod\s+(-R\s+)?777\b",
    r"\bchown\s+-R\b",
    r"(curl|wget)[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b",
    r">\s*/dev/sd[a-z]",
    r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE)\b",
    r"\bterraform\s+(destroy|apply)\b",
    r"\baws\s+\S+\s+(delete|terminate|remove)-",
    r"\bkubectl\s+delete\b",
    r"\bdocker\s+(system\s+prune|rm\s+-f)",
    r":\(\)\s*\{",
]
DANGER_RE = re.compile("|".join(DANGER), re.IGNORECASE)

TOOL_TITLES = {
    "Bash": "Ejecutar comando",
    "Edit": "Editar archivo",
    "MultiEdit": "Editar archivo",
    "Write": "Crear archivo",
    "NotebookEdit": "Editar notebook",
    "Read": "Leer archivo",
    "Glob": "Buscar archivos",
    "Grep": "Buscar en archivos",
    "WebFetch": "Abrir página web",
    "WebSearch": "Buscar en la web",
    "Agent": "Lanzar subagente",
    "Task": "Lanzar subagente",
}

MAX_LINES = 14


def _s(v):
    """Cualquier valor como texto (las entradas vienen de afuera y pueden ser null o numeros)."""
    return "" if v is None else v if isinstance(v, str) else str(v)


def _short_path(path, cwd):
    if not path:
        return ""
    path = _s(path)
    if cwd and path.startswith(cwd.rstrip("/") + "/"):
        return path[len(cwd.rstrip("/")) + 1:]
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home) else path


def _clip(text, lines=MAX_LINES):
    rows = _s(text).splitlines() or [""]
    if len(rows) > lines:
        rows = rows[:lines] + [f"… (+{len(rows) - lines} líneas)"]
    return "\n".join(r if len(r) < 400 else r[:400] + "…" for r in rows)


def _diff(old, new):
    rows = [f"- {l}" for l in _s(old).splitlines()] + [f"+ {l}" for l in _s(new).splitlines()]
    return _clip("\n".join(rows))


def _as_dict(inp):
    if isinstance(inp, dict):
        return inp
    return {} if inp is None else {"valor": inp}


def describe(tool, inp, cwd=""):
    """Devuelve dict con title, subtitle, body, bodyKind ('code'|'diff'|'text'), danger."""
    inp = _as_dict(inp)
    tool = tool if isinstance(tool, str) else str(tool)
    title = TOOL_TITLES.get(tool, tool)
    subtitle, body, kind = "", "", "code"

    if tool == "Bash":
        subtitle = inp.get("description") or ""
        body = _clip(_s(inp.get("command")))
    elif tool in ("Edit", "MultiEdit"):
        subtitle = _short_path(inp.get("file_path"), cwd)
        if tool == "MultiEdit":
            parts = [_diff(e.get("old_string"), e.get("new_string")) for e in (inp.get("edits") or []) if isinstance(e, dict)]
            body = _clip("\n".join(parts))
        else:
            body = _diff(inp.get("old_string"), inp.get("new_string"))
        kind = "diff"
    elif tool == "Write":
        subtitle = _short_path(inp.get("file_path"), cwd)
        body = _clip(inp.get("content", ""), 10)
    elif tool == "Read":
        subtitle = _short_path(inp.get("file_path"), cwd)
    elif tool in ("Glob", "Grep"):
        subtitle = inp.get("pattern", "")
        if inp.get("path"):
            body = _short_path(inp["path"], cwd)
    elif tool == "WebFetch":
        subtitle = inp.get("url", "")
        body, kind = inp.get("prompt", ""), "text"
    elif tool == "WebSearch":
        subtitle = inp.get("query", "")
    elif tool in ("Agent", "Task"):
        subtitle = inp.get("description", "")
        body, kind = _clip(inp.get("prompt", ""), 6), "text"
    elif tool.startswith("mcp__"):
        _, server, *name = tool.split("__")
        title = f"MCP · {server}"
        subtitle = "__".join(name)
        body = _clip(json.dumps(inp, indent=2, ensure_ascii=False))
    else:
        body = _clip(json.dumps(inp, indent=2, ensure_ascii=False))

    scan = _s(inp.get("command")) if tool == "Bash" else ""
    return {
        "title": title,
        "subtitle": subtitle,
        "body": body,
        "bodyKind": kind,
        "danger": bool(scan and DANGER_RE.search(scan)),
    }


def activity(tool, inp, cwd=""):
    """Linea corta de 'que esta haciendo' para la lista de sesiones."""
    inp = _as_dict(inp)
    tool = tool if isinstance(tool, str) else str(tool)
    if tool == "Bash":
        return "$ " + (_s(inp.get("command")).splitlines() or [""])[0][:120]
    if tool in ("Edit", "MultiEdit", "Write", "Read", "NotebookEdit"):
        verb = {"Read": "Leyendo", "Write": "Creando"}.get(tool, "Editando")
        return f"{verb} {_short_path(inp.get('file_path') or inp.get('notebook_path'), cwd)}"
    if tool in ("Glob", "Grep"):
        return f"Buscando {inp.get('pattern', '')}"
    if tool == "WebFetch":
        return f"Abriendo {inp.get('url', '')}"
    if tool == "WebSearch":
        return f"Buscando «{inp.get('query', '')}»"
    if tool in ("Agent", "Task"):
        return f"Subagente: {inp.get('description', '')}"
    if tool == "AskUserQuestion":
        first = (inp.get("questions") or [{}])[0].get("question", "")
        return f"Te pregunta: {first}" if first else "Te hace una pregunta"
    if tool.startswith("mcp__"):
        return "MCP · " + " › ".join(tool.split("__")[1:])
    return tool
