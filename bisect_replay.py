import can
import time
import sys

# 설정: 인터페이스 이름 (Kali에서 보통 can0 또는 vcan0)
CHANNEL = 'vcan0' 
BITRATE = 500000

def parse_log(logfile):
    """
    candump 포맷 파싱 (예: (162000.000) vcan0 123 [8] 11 22 33 ...)
    또는 단순 ID#DATA 포맷 등 상황에 맞춰 수정 필요.
    여기서는 (ID, Data) 튜플 리스트로 리턴한다고 가정.
    """
    packets = []
    # [MVP] 테스트를 위한 더미 데이터 생성 (실제 사용 시엔 파일 읽기로 대체)
    print("[*] Loading log file...")
    for i in range(100):
        packets.append(can.Message(arbitration_id=0x100+i, data=[0x00, 0x00, 0x00, 0x00], is_extended_id=False))
    
    # 정답(Target) 패킷 심어두기 (테스트용)
    packets[55].data = [0xFF, 0xFF, 0xFF, 0xFF] 
    print(f"[*] Loaded {len(packets)} packets.")
    return packets

def send_packets(bus, packet_list):
    print(f"[*] Sending {len(packet_list)} packets...")
    for msg in packet_list:
        try:
            bus.send(msg)
            time.sleep(0.001) # 패킷 간 딜레이 (필요 시 조정)
        except can.CanError:
            print("Message NOT sent")

def bisect(bus, packet_list):
    if len(packet_list) == 1:
        return packet_list[0]

    mid = len(packet_list) // 2
    first_half = packet_list[:mid]
    second_half = packet_list[mid:]

    print(f"\n--- Range: {len(packet_list)} packets left ---")
    print(f"1. Send First Half ({len(first_half)} packets)")
    print(f"2. Send Second Half ({len(second_half)} packets)")
    
    # 1번 그룹 전송
    print(">> Sending First Half...")
    send_packets(bus, first_half)
    
    ans = input(">> Did the target action happen? (y/n): ").strip().lower()
    
    if ans == 'y':
        print("[+] Target is in the first half.")
        return bisect(bus, first_half)
    else:
        print("[-] Target must be in the second half.")
        return bisect(bus, second_half)

if __name__ == "__main__":
    try:
        bus = can.interface.Bus(channel=CHANNEL, bustype='socketcan')
    except:
        print(f"[!] Error: Could not open {CHANNEL}. Using Virtual mode for testing.")
        # 실제 연결 안될 때 로직 테스트용 (주석 처리 가능)
        bus = None 

    # 실제 로그 파일이 있다면: packets = parse_log("candump.log")
    packets = parse_log("dummy") 
    
    print("[*] Starting Binary Search Replay Attack...")
    input("Press Enter to start...")
    
    culprit = bisect(bus, packets)
    
    print("\n" + "="*30)
    print(f"Found Culprit Packet!")
    print(f"ID: {hex(culprit.arbitration_id)}")
    print(f"Data: {culprit.data.hex()}")
    print("="*30)