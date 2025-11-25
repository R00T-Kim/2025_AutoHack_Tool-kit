import cantools
import can

# 1. DBC 파일 로드 (현장에서 파일명 수정)
db = cantools.database.load_file('vehicle_can.dbc')

def decode_msg(id, data):
    try:
        # DBC에서 ID로 메시지 찾기
        message = db.get_message_by_frame_id(id)
        # 데이터 디코딩
        signals = db.decode_message(id, data)
        print(f"[ID: {hex(id)}] {message.name}: {signals}")
    except KeyError:
        # DBC에 없는 ID
        # print(f"[Unknown ID] {hex(id)}")
        pass
    except Exception as e:
        print(f"[Error] {e}")

# 2. 실시간 디코딩 (Live)
bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
print("[*] Decoding CAN Stream with DBC...")

for msg in bus:
    decode_msg(msg.arbitration_id, msg.data)
