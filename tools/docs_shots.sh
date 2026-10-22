#!/usr/bin/env bash
# Regenera las capturas de docs/img con la demo (datos de ejemplo) sobre un fondo neutro.
# Recorta según la posición real de las ventanas de la app.
cd "$(dirname "$0")/.."
SP=$(mktemp -d)
geom() {  # $1 = tipo de ventana (UTILITY = panel, NOTIFICATION = avisos) -> "WxH+X+Y" que las abarca a todas
  local pids; pids=" $(pgrep -f "claudetray --demo" | tr '\n' ' ') "
  for id in $(xwininfo -root -tree | awk '/^ +0x[0-9a-f]+ /{print $1}'); do
    case "$pids" in *" $(xprop -id "$id" _NET_WM_PID 2>/dev/null | awk '{print $3}') "*) ;; *) continue ;; esac
    xprop -id "$id" _NET_WM_WINDOW_TYPE | grep -q "_NET_WM_WINDOW_TYPE_$1" || continue
    xwininfo -id "$id" | grep -q "IsViewable" || continue
    xwininfo -id "$id" | awk '/Absolute upper-left X/{x=$4}/Absolute upper-left Y/{y=$4}/Width:/{w=$2}/Height:/{h=$2}END{print x, y, w, h}'
  done | if [ "$1" = UTILITY ]; then sort -k5 -n -r <(awk '{print $0, $3*$4}') | head -1; else cat; fi \
       | awk 'NR==1{x0=$1;y0=$2;x1=$1+$3;y1=$2+$4} {if($1<x0)x0=$1; if($2<y0)y0=$2; if($1+$3>x1)x1=$1+$3; if($2+$4>y1)y1=$2+$4}
              END{if(x0<0)x0=0; if(y0<0)y0=0; printf "%dx%d+%d+%d", x1-x0, y1-y0, x0, y0}'
}
shot() {  # $1 = args de la demo, $2 = tipo de ventana, $3 = archivo
  local g=""
  for try in 1 2 3; do                     # a veces la ventana aun no esta lista: se reintenta
    ARGS="$1" DELAY=${WAIT:-4} tools/shoot.sh "$SP" >/dev/null 2>&1
    g=$(geom "$2")
    case "$g" in ""|0x0*) continue ;; esac
    convert "$SP/shot.png" -crop "$g" +repage "docs/img/$3" && echo "$3  $g"
    return
  done
  echo "$3: no se pudo capturar"
}
shot "--corner"              NOTIFICATION  notificaciones.png
shot "--bubble"              NOTIFICATION  burbuja.png
shot "--corner"              UTILITY       panel.png
shot "--corner --pet"        UTILITY       mascota.png
shot "--corner --question"   NOTIFICATION  pregunta.png
shot "--corner --usage"      UTILITY       consumo.png
shot "--corner --pet-edit"   UTILITY       ajustes.png
rm -rf "$SP"
