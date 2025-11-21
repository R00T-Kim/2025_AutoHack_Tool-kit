import can
import time
from collections import defaultdict

CHANNEL = 'vcan0'
LEARNING_TIME = 5 

class IntelligentIDS:
    def __init__(self):
        self.bus = can.interface.Bus(channel=CHANNEL, bustype='socketcan')
        self.whitelist_interval = {} 
        self.last_seen = {}
        self.last_payload = {} # [Chapter 5] Payload 변경 추적용
        
        # 해커들이 주로 쓰는 진단/공격 ID 및 패턴 (Signature Based)
        self.blacklisted_ids = [0x7DF] # OBD-II Broadcast ID
        self.suspicious_payloads = [
            b'\x02\x10\x03', # Extended Diagnostic Session Request
            b'\x02\x3E\x00', # Tester Present (Keep-Alive)
        ]

    def learn_mode(self):
        print(f"[*] Learning normal traffic patterns & Payloads ({LEARNING_TIME}s)...")
        start_time = time.time()
        intervals = defaultdict(list)
        
        while time.time() - start_time < LEARNING_TIME:
            msg = self.bus.recv(timeout=1.0)
            if not msg: continue
            
            aid = msg.arbitration_id
            now = time.time()
            
            if aid in self.last_seen:
                intervals[aid].append(now - self.last_seen[aid])
            
            self.last_seen[aid] = now
            self.last_payload[aid] = msg.data # 정상 상태의 마지막 페이로드 저장

        # 기준 수립
        for aid, times in intervals.items():
            if times:
                avg = sum(times) / len(times)
                self.whitelist_interval[aid] = avg * 0.5 # 50% 마진
                print(f"  [Learned] ID: {hex(aid)} Interval: {avg:.4f}s")

    def detect_payload_anomaly(self, aid, new_data):
        """
        [Chapter 5] Data Analysis logic
        이전 데이터와 비교해서 급격한 변화나 이상 패턴 감지
        """
        if aid not in self.last_payload:
            return False
            
        old_data = self.last_payload[aid]
        
        # 간단한 휴리스틱: 데이터가 완전히 바뀌었는지 확인 (Fuzzing 징후)
        # 실제로는 Hamming Distance나 비트 단위 분석이 필요함
        diff_count = sum(1 for a, b in zip(old_data, new_data) if a != b)
        
        if diff_count > 6: # 8바이트 중 6바이트 이상이 한 번에 바뀌면 의심
            return True
            
        return False

    def detect_protocol_attack(self, msg):
        """
        [Chapter 4 & 6] UDS/Diagnostics Attack Detection
        주행 중(Monitor Mode)에 진단 패킷이 날아오면 100% 해킹 시도임.
        """
        # 1. Known Hack ID Check
        if msg.arbitration_id in self.blacklisted_ids:
            return f"Blacklisted ID Detected: {hex(msg.arbitration_id)}"

        # 2. UDS Service Attack Check (데이터 앞부분 확인)
        # ISO-TP Single Frame(0x)이면서 Service ID가 0x10(Session), 0x23(ReadMem) 등인지 확인
        if msg.data and len(msg.data) > 2:
            pci = msg.data[0]
            sid = msg.data[1]
            
            # Single Frame & (Diagnostic Session or ReadMemory or WriteMemory)
            if (pci & 0xF0 == 0) and (sid in [0x10, 0x23, 0x3D, 0x27]):
                return f"Critical UDS Attack Detected! Service: {hex(sid)}"
        
        return None

    def monitor_mode(self):
        print("\n[*] INTELLIGENT IDS ACTIVE. Monitoring...")
        while True:
            msg = self.bus.recv()
            if not msg: continue
            
            aid = msg.arbitration_id
            now = time.time()

            # 1. Frequency Analysis (DoS / Injection)
            if aid in self.last_seen:
                delta = now - self.last_seen[aid]
                if aid in self.whitelist_interval and delta < self.whitelist_interval[aid]:
                    print(f"[!!!] TIMING ANOMALY: ID {hex(aid)} (Too fast: {delta:.4f}s)")

            # 2. Protocol & Signature Analysis (Hacking Attempts)
            alert = self.detect_protocol_attack(msg)
            if alert:
                print(f"\n[CRITICAL] {alert} | Payload: {msg.data.hex()}")

            # 3. Payload Anomaly (Fuzzing / Spoofing)
            if self.detect_payload_anomaly(aid, msg.data):
                print(f"[!] PAYLOAD ANOMALY: ID {hex(aid)} changed significantly!")
                print(f"    Old: {self.last_payload[aid].hex()} -> New: {msg.data.hex()}")

            # 상태 업데이트
            self.last_seen[aid] = now
            self.last_payload[aid] = msg.data

if __name__ == "__main__":
    ids = IntelligentIDS()
    try:
        ids.learn_mode()
        ids.monitor_mode()
    except KeyboardInterrupt:
        print("[-] IDS Stopped.")
