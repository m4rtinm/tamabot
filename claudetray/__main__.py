import sys

# --version y los comandos de control (--allow, --deny, --panel, --terminal) no necesitan Qt:
# se atienden antes de importarlo, asi funcionan aunque falten librerias graficas.
from .cli import handle

code = handle(sys.argv)
if code is None:
    from .app import main
    code = main()
sys.exit(code)
