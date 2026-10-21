# test_boot.py  (테스트 끝나면 삭제)

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from boot import api as boot_client   # ← 1번에서 찾은 파일 이름으로 (.py 빼고)

now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

payload = {
    "dl_camera_id": "CAM-TEST",
    "dl_zone_no": "1",
    "dl_violation_type": "TEST",
    "dl_car_number": "12가3456",
    "dl_first_detected_at": now,
    "dl_last_detected_at": now,
    "dl_image_path": "http://http://192.168.0.141:5000/images/test.jpg"
}

dl_no = boot_client.post_detection(payload)
print("저장된 dl_no:", dl_no)