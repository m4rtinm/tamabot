#!/usr/bin/env bash
# Lista las ventanas X de Tamabot con su estado, geometria y region de blur.
PID=$(pgrep -f "m tamabot" | tail -1)
for id in $(xwininfo -root -tree | awk '/0x[0-9a-f]+ /{print $1}'); do
  p=$(xprop -id $id _NET_WM_PID 2>/dev/null | awk '{print $3}')
  [ "$p" = "$PID" ] || continue
  echo "$id | $(xwininfo -id $id | grep -E 'Map State|geometry|Depth' | xargs) | $(xprop -id $id _KDE_NET_WM_BLUR_BEHIND_REGION _NET_WM_STATE _NET_WM_WINDOW_OPACITY 2>/dev/null | cut -c1-70 | xargs)"
done
