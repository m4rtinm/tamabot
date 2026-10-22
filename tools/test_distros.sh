#!/usr/bin/env bash
# Prueba el instalador en contenedores de varias distros, siguiendo sus propias instrucciones:
# 1) instala, 2) ejecuta el comando de paquetes que sugiere, 3) reinstala y abre la app (sin pantalla).
# Uso: tools/test_distros.sh [ubuntu:24.04 debian:12 fedora:41 archlinux:latest]
cd "$(dirname "$0")/.."
DISTROS=${*:-"ubuntu:24.04 debian:12 fedora:41 archlinux:latest"}
for img in $DISTROS; do
  case $img in
    ubuntu*|debian*) prep="apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv curl ca-certificates >/dev/null" ;;
    fedora*) prep="dnf install -y -q python3 >/dev/null" ;;
    arch*) prep="pacman -Sy --noconfirm --quiet python >/dev/null" ;;
  esac
  echo "================ $img ================"
  docker run --rm -v "$PWD":/src:ro "$img" sh -c "
    $prep
    export DEBIAN_FRONTEND=noninteractive PATH=/root/.local/bin:\$PATH
    cp -r /src /tmp/app && cd /tmp/app && rm -rf .venv
    mkdir -p /root/.claude && echo '{\"model\": \"opus\"}' > /root/.claude/settings.json
    python3 install.py --yes --no-start > /tmp/i1.log 2>&1; code=\$?
    echo \"[1ª instalación: código \$code]\"; grep -E '✗|instálala|Instálala|Python 3.12' /tmp/i1.log | head -4
    if grep -q 'instalar uv' /tmp/i1.log; then
      echo '[siguiendo el consejo: instalar uv]'
      curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
    fi
    cmd=\$(grep -ohE '(sudo )?(apt install|dnf install|pacman -S|zypper install) [a-z0-9 .+_-]+' /tmp/i1.log | grep -v python | head -1 | sed 's/^sudo //')
    if [ -n \"\$cmd\" ]; then
      echo \"[siguiendo el consejo: \$cmd]\"
      case \$cmd in apt*) cmd=\"apt-get install -y -qq \${cmd#apt install }\";; dnf*) cmd=\"\$cmd -y -q\";; pacman*) cmd=\"\$cmd --noconfirm\";; esac
      sh -c \"\$cmd\" >/dev/null 2>&1 || echo '  (el comando sugerido falló)'
    fi
    python3 install.py --yes --no-start > /tmp/i2.log 2>&1; code=\$?
    echo \"[2ª instalación: código \$code]\"; grep -E '✓|✗|Qt carga|Qt no puede|falta' /tmp/i2.log | head -4
    if [ \$code = 0 ]; then
      traychi --version
      export QT_QPA_PLATFORM=offscreen XDG_RUNTIME_DIR=/tmp/rt; mkdir -p -m 700 /tmp/rt
      timeout 6 traychi >/tmp/run.log 2>&1; rc=\$?
      [ \$rc = 124 ] && echo '[la app abrió y siguió corriendo 6 s: OK]' || { echo \"[la app terminó con código \$rc]\"; tail -5 /tmp/run.log; }
      grep -iE 'error|traceback' /root/.cache/traychi/traychi.log | head -3
      python3 -c \"import json; d=json.load(open('/root/.claude/settings.json')); print('[hooks:', len(d['hooks']), 'eventos; model conservado:', d.get('model'), ']')\"
      python3 install.py --uninstall >/dev/null && echo '[desinstalación ok]'
    fi
  " 2>&1 | grep -v "Pulling\|Download\|Pull complete\|Digest\|Status:\|debconf" | tail -25
done
