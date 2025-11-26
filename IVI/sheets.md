# OS 버전 및 커널 확인
uname -a

# QNX라면 'pidin' 명령이 먹힘
pidin info  # 동작하면 QNX일 가능성 매우 높음

pidin a | head
mount


# 'display', 'power', 'backlight' 키워드로 검색
ls -R /pps/ | grep -i "display"
ls -R /pps/ | grep -i "backlight"
ls -R /pps/ | grep -i "power"

# 현재 설정값 확인 (Key::Value 형태 파악)
cat /pps/services/display/control
cat /pps/services/backlight/control

# 화면 끄기 (전원 Off 계열)
echo "display_power::off"  >> /pps/services/display/control
echo "power::off"          >> /pps/services/display/control

# (대안) 밝기 0으로 암전 (화면은 켜져 있으나 사실상 Black)
echo "brightness::0"       >> /pps/services/backlight/control
echo "backlight::off"      >> /pps/services/backlight/control  # 있으면 같이 시도

# 화면 관련 프로세스 후보 검색
pidin a | grep -E "HMI|Mib|Eso|Display|Layer|Nav|LSD"


# init 스크립트 중 HMI/Display 관련된 것 찾기
ls /etc/init.d
grep -R "HMI" /etc/init.d 2>/dev/null
grep -R "Mib" /etc/init.d 2>/dev/null

# 발견되면 stop 먼저 시도 (예시)
 /etc/init.d/rc.hmi stop   2>/dev/null || true
 /etc/init.d/hmi    stop   2>/dev/null || true

# QNX slay 사용
slay -9 MibStandard   2>/dev/null
slay -9 EsoHmi        2>/dev/null
slay -9 LayerManager  2>/dev/null
slay -9 LSD           2>/dev/null

# 만약 Linux 계열이라면 (후보)
kill -9 $(pidof MibStandard)   2>/dev/null
kill -9 $(pidof EsoHmi)        2>/dev/null

ls /dev/fb*
ls /dev/graphics/
ls /dev/screen/

# 검은 화면 (0값으로 화면 전체 덮기)
cat /dev/zero > /dev/fb0
# 또는
dd if=/dev/zero of=/dev/fb0 bs=1M

# 랜덤 데이터로 화면 덮기 (노이즈)
cat /dev/urandom > /dev/fb0
# 또는
dd if=/dev/urandom of=/dev/fb0 bs=1M count=8

# 부드러운 재부팅
shutdown
reboot

# QNX에서 커널 프로세스를 죽여 강제 리부트 (매우 거칠다)
slay -9 procnto

