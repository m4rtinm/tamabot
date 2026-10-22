#!/usr/bin/env bash
# Muestra tipo de ventana y si acepta foco, para cada ventana de la demo en curso.
PID=$(pgrep -f "tamabot --demo" | tail -1)
for id in $(xwininfo -root -tree | awk '/0x[0-9a-f]+ /{print $1}'); do
  [ "$(xprop -id $id _NET_WM_PID 2>/dev/null | awk '{print $3}')" = "$PID" ] || continue
  g=$(xwininfo -id $id | grep -o "geometry [0-9x+-]*")
  h=$(xprop -id $id WM_HINTS | grep -i "input" | xargs)
  t=$(xprop -id $id _NET_WM_WINDOW_TYPE | cut -d= -f2 | cut -c1-45)
  echo "$g | $h | $t"
done
