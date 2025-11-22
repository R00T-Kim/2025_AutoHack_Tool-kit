from djitellopy import Tello
import time
import sys

def init_drone():
    print("[*] Tello 드론 연결 시도 중...")
    drone = Tello()
    
    try:
        drone.connect()
        print("[+] 드론 연결 성공!")
        
        # 배터리 체크 (가장 중요)
        battery = drone.get_battery()
        print(f"[*] 현재 배터리 잔량: {battery}%")
        
        if battery < 20:
            print("[!] 경고: 배터리가 부족합니다. 비행을 권장하지 않습니다.")
            choice = input(">> 그래도 진행하시겠습니까? (y/n): ")
            if choice.lower() != 'y':
                sys.exit(0)
                
        return drone
    except Exception as e:
        print(f"[-] 연결 실패: {e}")
        print("    (Tip: PC의 Wi-Fi가 Tello에 연결되어 있는지 확인하십시오)")
        sys.exit(1)

def flight_routine(drone):
    try:
        print("\n[Ready] 엔터 키를 누르면 이륙합니다 (Takeoff)...")
        input()
        
        print("[↑] 이륙 중...")
        drone.takeoff()
        time.sleep(2) # 안정화 대기

        print("[*] 호버링 상태 유지 (5초)")
        # 여기서 추가 공격 시나리오(영상 탈취 등)를 수행할 수 있음
        for i in range(5, 0, -1):
            print(f"    {i}...", end='\r')
            time.sleep(1)
        print("")

        # 전진/후진 테스트 (제어권 증명용)
        print("[*] 제어권 확인: 전진 20cm")
        drone.move_forward(20)
        time.sleep(2)

        print("[*] 제어권 확인: 후진 20cm")
        drone.move_back(20)
        time.sleep(2)

        print("\n[Ready] 엔터 키를 누르면 착륙합니다 (Land)...")
        input()
        
        print("[↓] 착륙 중...")
        drone.land()
        print("[+] 착륙 완료.")

    except KeyboardInterrupt:
        print("\n[!!!] 긴급 중단(Ctrl+C) 감지! 비상 착륙 시도...")
        drone.land()
    except Exception as e:
        print(f"[-] 비행 중 오류 발생: {e}")
        print("    비상 착륙 시도...")
        try:
            drone.land()
        except:
            print("[-] 비상 착륙 실패. 강제 종료.")

if __name__ == "__main__":
    print("=== AutoHack 2025 Tello Controller ===")
    
    # 1. 드론 객체 초기화 및 연결
    my_drone = init_drone()
    
    # 2. 비행 시나리오 실행
    flight_routine(my_drone)
    
    # 3. 연결 종료
    my_drone.end()
