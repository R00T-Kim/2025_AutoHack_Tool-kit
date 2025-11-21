# 2025_AutoHack_Tool-kit
---
1. bisect_replay.py
- 이진 탐색 Replay 툴

2. simple_ids.py
- Rule-based IDS

3. isotp_decoder.py
- ISO-TP 추출기

4. video_stego.py
- 동영상 OCR 스크립트

---

가상 CAN 설정 (로컬 테스트용):

```Bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```
OCR 준비:

Ubuntu: sudo apt install tesseract-ocr libtesseract-dev

Python: pip install pytesseract opencv-python

전략:

Replay: 무작위로 하지 말고 bisect_replay.py로 범위를 확실히 좁힐 것.

IDS: 대회 시작하자마자 정상 상태에서 simple_ids.py를 켜서 1분간 학습(Learn) 시키고 로그를 확보할 것.

ISO-TP: 덤프 파일이 주어지면 isotp_decoder.py 로직을 참고해 파싱할 것.