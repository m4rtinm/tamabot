"""Todo Text de la interfaz debe fijar su formato: el AutoText por defecto de QML
interpreta HTML, y el contenido (comandos, rutas, mensajes) viene de afuera."""
import re
from pathlib import Path

QML = Path(__file__).resolve().parent.parent / "traychi" / "qml"


def text_blocks(src):
    for m in re.finditer(r"\bText \{", src):
        depth, j = 1, m.end()
        while depth:
            depth += (src[j] == "{") - (src[j] == "}")
            j += 1
        body = src[m.end():j - 1]
        yield src.count("\n", 0, m.start()) + 1, re.sub(r"\b\w+ \{[^{}]*\}", "", body)


def test_ningun_texto_interpreta_html():
    sin_formato = [f"{p.name}:{line}" for p in QML.glob("*.qml")
                   for line, body in text_blocks(p.read_text()) if "textFormat" not in body]
    assert not sin_formato, f"Text sin textFormat (usa Text.PlainText): {sin_formato}"


def test_los_textos_con_formato_escapan_el_contenido():
    for p in QML.glob("*.qml"):
        src = p.read_text()
        for line, body in text_blocks(src):
            if "Text.StyledText" in body and "esc(" not in body and "<b>" in body:
                # se permite StyledText solo con contenido propio o escapado
                assert "ctrl." not in body and "s." not in body, f"{p.name}:{line} sin escapar"
