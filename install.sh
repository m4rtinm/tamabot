#!/bin/sh
# Instalador de Claude Tray. Uso:  ./install.sh   (o ./install.sh --uninstall)
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
    echo "Hace falta python3 para instalar. Instálalo y vuelve a ejecutar:"
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-venv"
    echo "  Fedora:         sudo dnf install python3"
    echo "  Arch:           sudo pacman -S python"
    echo "  openSUSE:       sudo zypper install python3"
    exit 1
fi
exec python3 install.py "$@"
