import can

# ISO-TP Frame Types
SINGLE_FRAME = 0
FIRST_FRAME = 1
CONSECUTIVE_FRAME = 2
FLOW_CONTROL = 3

buffer = {} # {id: {'data': bytearray, 'length': int, 'idx': int}}

def decode_isotp(msg):
    """
    CAN 메시지를 받아 ISO-TP 로직으로 조립 시도
    """
    aid = msg.arbitration_id
    data = msg.data
    if not data: return

    pci_type = (data[0] & 0xF0) >> 4
    
    # 1. Single Frame (데이터가 짧을 때)
    if pci_type == SINGLE_FRAME:
        length = data[0] & 0x0F
        payload = data[1:1+length]
        try_print_flag(aid, payload)

    # 2. First Frame (긴 데이터의 시작)
    elif pci_type == FIRST_FRAME:
        total_length = ((data[0] & 0x0F) << 8) | data[1]
        payload = data[2:]
        buffer[aid] = {
            'data': bytearray(payload),
            'length': total_length,
            'expected_sn': 1
        }
        # [중요] 실제 통신에선 여기서 Flow Control을 보내줘야 하지만,
        # CTF에서 Sniffing만 하는 경우라면 그냥 수신만 대기.

    # 3. Consecutive Frame (이어지는 데이터)
    elif pci_type == CONSECUTIVE_FRAME:
        if aid not in buffer: return
        
        sn = data[0] & 0x0F
        if sn != buffer[aid]['expected_sn']:
            # Sequence Number 불일치 (패킷 로스 등) -> 초기화
            # del buffer[aid] # 엄격하게 하려면 삭제, CTF에선 그냥 진행
            pass
            
        payload = data[1:]
        buffer[aid]['data'].extend(payload)
        buffer[aid]['expected_sn'] = (sn + 1) % 16
        
        # 다 모았는지 확인
        if len(buffer[aid]['data']) >= buffer[aid]['length']:
            full_data = buffer[aid]['data'][:buffer[aid]['length']]
            try_print_flag(aid, full_data)
            del buffer[aid]

def try_print_flag(aid, data_bytes):
    try:
        decoded = data_bytes.decode('utf-8', errors='ignore')
        # 플래그 패턴이 보이거나, 읽을 수 있는 문자열이 길면 출력
        if "FLAG" in decoded or "Key" in decoded or len(decoded) > 5:
            print(f"\n[+] Reassembled ISO-TP (ID: {hex(aid)})")
            print(f"    Hex: {data_bytes.hex()}")
            print(f"    Str: {decoded}")
    except:
        pass

if __name__ == "__main__":
    # [MVP] 테스트용 데이터 (First Frame -> Consecutive Frames)
    # 예: "FLAG{CAN_IS_FUN}" (16 bytes)
    # FF: 10 10 46 4C 41 47 7B 43 (Length: 16, Data: FLAG{C)
    # CF: 21 41 4E 5F 49 53 5F 46 (Data: AN_IS_F)
    # CF: 22 55 4E 7D 00 00 00 00 (Data: UN})
    
    msgs = [
        can.Message(arbitration_id=0x7E8, data=[0x10, 0x10, 0x46, 0x4C, 0x41, 0x47, 0x7B, 0x43]),
        can.Message(arbitration_id=0x7E8, data=[0x21, 0x41, 0x4E, 0x5F, 0x49, 0x53, 0x5F, 0x46]),
        can.Message(arbitration_id=0x7E8, data=[0x22, 0x55, 0x4E, 0x7D, 0x00, 0x00, 0x00, 0x00])
    ]
    
    print("[*] Decoding ISO-TP Stream...")
    for m in msgs:
        decode_isotp(m)