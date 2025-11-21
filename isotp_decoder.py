import can
import time
import struct

# ISO-TP Frame Types
SINGLE_FRAME = 0
FIRST_FRAME = 1
CONSECUTIVE_FRAME = 2
FLOW_CONTROL = 3

# UDS Constants
SERVICE_DIAG_SESSION = 0x10
SERVICE_SEC_ACCESS = 0x27

class UDSSecurityScanner:
    def __init__(self, channel='vcan0'):
        self.bus = can.interface.Bus(channel=channel, bustype='socketcan')
        self.buffer = {}  # Reassembly Buffer

    def send_flow_control(self, aid):
        """
        [Chapter 4] ISO-TP Flow Control 전송
        ECU에게 '나 준비됐으니 나머지 데이터(CF)를 보내라'고 신호함.
        Response ID는 보통 Request ID + 8 (예: 0x7E0 -> 0x7E8)
        여기서는 수신한 ID(aid)에 대해 응답하므로, 타겟 ECU가 보낸 ID를 그대로 타겟팅.
        """
        # Flow Control Frame: [30, BS, STmin, ...]
        # 0x30: FlowControl, ContinueToSend
        # 0x00: BlockSize (0=unlimited)
        # 0x00: STmin (Minimum Separation Time, 0=fastest)
        fc_frame = [0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        # 보통 ECU 응답 ID에서 8을 빼면 요청 ID가 됨 (예: 7E8 -> 7E0)
        # 하지만 여기선 Sniffing 중이므로 역으로 계산 필요하거나,
        # 능동 공격시엔 타겟 ID를 알고 있어야 함. 
        # *실습용으로 0x7E0(Engine)를 가정하고 0x7E0으로 FC를 쏜다고 가정*
        target_req_id = aid - 0x8 
        
        msg = can.Message(arbitration_id=target_req_id, data=fc_frame, is_extended_id=False)
        try:
            self.bus.send(msg)
            print(f"[->] Sent Flow Control to {hex(target_req_id)}")
        except can.CanError:
            print("[-] Failed to send Flow Control")

    def scan_security_access(self, target_id):
        """
        [Chapter 6] 0x27 Security Access Seed 요청
        """
        print(f"[*] Attacking Target {hex(target_id)} for Seed...")
        
        # 1. Extended Session (0x10 0x03) 진입 시도
        print(f"[->] Requesting Extended Session to {hex(target_id)}...")
        msg = can.Message(arbitration_id=target_id, data=[0x02, 0x10, 0x03, 0, 0, 0, 0, 0], is_extended_id=False)
        self.bus.send(msg)
        time.sleep(0.1) # ECU 처리 대기

        # 2. Seed 요청 (0x27 0x01)
        print(f"[->] Requesting Security Seed to {hex(target_id)}...")
        msg = can.Message(arbitration_id=target_id, data=[0x02, 0x27, 0x01, 0, 0, 0, 0, 0], is_extended_id=False)
        self.bus.send(msg)

    def process_stream(self):
        print("[*] UDS/ISO-TP Scanner Running...")
        while True:
            msg = self.bus.recv()
            if not msg: continue
            
            aid = msg.arbitration_id
            data = msg.data
            pci_type = (data[0] & 0xF0) >> 4

            # --- ISO-TP Handling ---
            if pci_type == FIRST_FRAME:
                total_len = ((data[0] & 0x0F) << 8) | data[1]
                self.buffer[aid] = {'data': bytearray(data[2:]), 'length': total_len, 'sn': 1}
                print(f"[<] Received First Frame from {hex(aid)}. Length: {total_len}")
                
                # [핵심] FF를 받으면 즉시 FC를 쏴줘야 함!
                self.send_flow_control(aid)

            elif pci_type == CONSECUTIVE_FRAME:
                if aid in self.buffer:
                    payload = data[1:]
                    self.buffer[aid]['data'].extend(payload)
                    
                    # 완료 체크
                    if len(self.buffer[aid]['data']) >= self.buffer[aid]['length']:
                        full_data = self.buffer[aid]['data']
                        self.analyze_uds_response(aid, full_data)
                        del self.buffer[aid]

            elif pci_type == SINGLE_FRAME:
                length = data[0] & 0x0F
                self.analyze_uds_response(aid, data[1:1+length])

    def analyze_uds_response(self, aid, data):
        """
        UDS 응답 분석 (Chapter 4)
        """
        service = data[0]
        # Positive Response는 Request Service ID + 0x40
        if service == (SERVICE_SEC_ACCESS + 0x40): # 0x67
            seed = data[2:] # 보통 [67, SubFn, Seed...]
            print(f"\n[!!!] SECURITY SEED CAPTURED from {hex(aid)}!")
            print(f"      SEED: {seed.hex()}")
            print(f"      [Next Step] Calculate Key & Reply with 0x27 0x02\n")
        elif service == 0x7F: # Negative Response
            print(f"[-] Error Response from {hex(aid)}: Code {hex(data[2])}")

if __name__ == "__main__":
    scanner = UDSSecurityScanner()
    # 테스트 시나리오: 엔진 ECU(0x7E0)에 대해 시드 요청 시도
    # 별도 쓰레드나 터미널에서 실행하거나, 입력을 받아 실행
    # scanner.scan_security_access(0x7E0) 
    scanner.process_stream()
