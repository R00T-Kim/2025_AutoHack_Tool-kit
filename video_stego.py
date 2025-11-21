import cv2
import pytesseract
import os

# 설정
VIDEO_PATH = 'challenge.mp4'
OUTPUT_DIR = 'extracted_frames'
KEYWORDS = ['FLAG', 'flag', '{', 'KEY', 'Password']

# Tesseract 경로 설정 (윈도우의 경우 필요, 리눅스는 보통 자동)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def solve_stego():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Error opening video file")
        return

    frame_count = 0
    detected_count = 0
    
    print(f"[*] Scanning video: {VIDEO_PATH}")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        
        # 속도 최적화: 10프레임마다 1번씩 검사 (너무 느리면 숫자 조절)
        if frame_count % 10 != 0:
            continue

        # OCR 정확도를 위한 전처리 (그레이스케일 -> 이진화)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 필요 시 Threshold 조절: ret, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        try:
            # OCR 수행
            text = pytesseract.image_to_string(gray).strip()
            
            # 키워드 검색
            for key in KEYWORDS:
                if key in text:
                    print(f"[+] Found '{key}' at Frame {frame_count}: {text}")
                    filename = f"{OUTPUT_DIR}/frame_{frame_count}.png"
                    cv2.imwrite(filename, frame)
                    detected_count += 1
                    break
        except Exception as e:
            print(f"[!] OCR Error: {e}")
            pass

        if frame_count % 100 == 0:
            print(f"Processing... {frame_count} frames done.")

    cap.release()
    print(f"\n[*] Finished. Found {detected_count} suspicious frames in '{OUTPUT_DIR}/'")

if __name__ == "__main__":
    solve_stego()