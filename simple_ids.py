import can
import time
from collections import defaultdict

CHANNEL = 'vcan0'
LEARNING_TIME = 5  # 5초 동안 정상 트래픽 학습
THRESHOLD = 0.5    # 학습된 주기의 50% 이하로 들어오면 공격으로 간주

whitelist = {} # {arb_id: min_interval}
last_seen = {} # {arb_id: timestamp}

def learn_mode(bus):
    print(f"[*] Learning normal traffic for {LEARNING_TIME} seconds...")
    start_time = time.time()
    temp_intervals = defaultdict(list)
    last_arrival = {}

    while time.time() - start_time < LEARNING_TIME:
        msg = bus.recv(timeout=1.0)
        if msg is None: continue
        
        now = time.time()
        aid = msg.arbitration_id
        
        if aid in last_arrival:
            interval = now - last_arrival[aid]
            temp_intervals[aid].append(interval)
        
        last_arrival[aid] = now

    # 평균 주기 계산 및 화이트리스트 등록
    print("[*] Building Whitelist...")
    for aid, intervals in temp_intervals.items():
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # 너무 짧은 주기로 들어오면 공격으로 간주 (허용 범위 설정)
            whitelist[aid] = avg_interval * THRESHOLD
            print(f"    ID: {hex(aid)} | Avg Interval: {avg_interval:.4f}s | Threshold: {whitelist[aid]:.4f}s")
    print("[*] Learning Complete.\n")

def monitor_mode(bus):
    print("[*] IDS Protection ACTIVE. Monitoring...")
    while True:
        msg = bus.recv()
        if msg is None: continue
        
        now = time.time()
        aid = msg.arbitration_id
        
        # 1. Whitelist Check (미등록 ID 탐지)
        if aid not in whitelist:
            print(f"[!!!] ALERT: Unknown ID Detected! ID: {hex(aid)} Data: {msg.data.hex()}")
            continue
            
        # 2. Frequency Check (Injection 탐지)
        if aid in last_seen:
            interval = now - last_seen[aid]
            if interval < whitelist[aid]:
                print(f"[!!!] ALERT: Injection Attack Detected! ID: {hex(aid)} Interval: {interval:.4f}s (Expected > {whitelist[aid]:.4f}s)")
        
        last_seen[aid] = now

if __name__ == "__main__":
    try:
        bus = can.interface.Bus(channel=CHANNEL, bustype='socketcan')
        learn_mode(bus)
        monitor_mode(bus)
    except Exception as e:
        print(f"[!] Error: {e}")