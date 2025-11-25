import sys

def parse_candump(logfile):
    print(f"[*] Parsing {logfile}...")
    with open(logfile, 'r') as f:
        for line in f:
            # 예: (162000.123) can0 123 [8] 11 22 33 ...
            try:
                parts = line.strip().split()
                timestamp = float(parts[0].strip('()'))
                interface = parts[1]
                arb_id = int(parts[2], 16)
                dlc = int(parts[3].strip('[]'))
                data = bytes.fromhex(''.join(parts[4:]))

                # [조건문 작성 구역] -------------------------
                # 예: ID가 0x123이고, 3번째 바이트가 0xFF인 것 찾기
                if arb_id == 0x123 and data[2] == 0xFF:
                    print(f"[FOUND] Time:{timestamp} ID:{hex(arb_id)} Data:{data.hex()}")
                # -------------------------------------------
            except Exception:
                continue

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 can_parser.py <logfile>")
    else:
        parse_candump(sys.argv[1])
