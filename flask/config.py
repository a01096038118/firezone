"""Flask AI 서버 설정. 대부분 환경변수로 바꿀 수 있다."""
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Flask 서버 ───────────────────────────────────
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
# Boot·브라우저가 사진·영상에 접근할 Flask 주소 (다른 PC에서 접근하면 이 PC의 IP로 변경)
FLASK_PUBLIC_URL = os.getenv("FLASK_PUBLIC_URL", f"http://localhost:{FLASK_PORT}")

# ── Boot 연동 (Boot 관리자 앱 firezonePjt_admin 기준) ──
# false 이면 Boot로 보내지 않고 보낼 내용만 로그로 출력 (Boot 없이 테스트용)
BOOT_ENABLED = os.getenv("BOOT_ENABLED", "true").lower() == "true"
BOOT_URL = os.getenv("BOOT_URL", "http://localhost:8090")
BOOT_DETECTION_API_PATH = os.getenv("BOOT_DETECTION_API_PATH", "/detections")
BOOT_REQUEST_TIMEOUT_SECONDS = float(os.getenv("BOOT_REQUEST_TIMEOUT_SECONDS", "3"))
# Boot에 수정 API(PUT /detections/{dl_no})가 생기면 true
BOOT_UPDATE_API_READY = os.getenv("BOOT_UPDATE_API_READY", "false").lower() == "true"
# Boot가 저장 요청을 CSRF로 막을 때(403) 토큰을 받아올 Boot 화면
BOOT_CSRF_TOKEN_PAGE_PATH = os.getenv("BOOT_CSRF_TOKEN_PAGE_PATH", "/admin/signin")
# Boot DetectionDto 의 LocalDateTime 이 읽는 시간 형식 (중간에 T)
BOOT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# ── 카메라 / 구역 ────────────────────────────────
# 카메라(드론) 목록. source: ESP32-CAM 스트림 주소 / 웹캠 번호("0") / 영상 파일 경로
CAMERAS = {
    "DRONE01": {
        "name": "드론 1 (ESP32-CAM)",
        "enabled": True,
        "source": os.getenv("DRONE01_SOURCE", "http://192.168.0.100:81/stream"),
        # 등록된 구역 사진과 맞지 않을 때 쓸 고정 구역. None 이면 판정 불가 (다른 아파트를 찍었을 때 잘못 단속하지 않게)
        "default_zone": None,
    },
}
ZONE_CONFIG_FILE = os.path.join(PROJECT_DIR, "zones", "zones.json")   # 구역 목록 (기준 사진 + 구역 테두리)
# 등록된 구역 사진과 맞지 않으면 바닥 표시(노란 테두리·빨간 빗금)로 구역을 직접 찾음
AUTO_ZONE_ENABLED = os.getenv("AUTO_ZONE_ENABLED", "true").lower() == "true"
AUTO_ZONE_NO = os.getenv("AUTO_ZONE_NO", "AUTO")          # 자동으로 찾은 구역의 구역번호 (Boot dl_zone_no)
AUTO_ZONE_MIN_AREA_RATIO = 0.03                           # 구역이 사진에서 최소 이 비율 이상 커야 함
AUTO_ZONE_MAX_PAINT_RATIO = 0.6                           # 구역 안이 이 비율 넘게 칠해져 있으면 벽·간판으로 보고 제외
AUTO_ZONE_MIN_OUTLINE_COVERAGE = 0.5                      # 구역 테두리를 따라 이 비율 이상 선이 그려져 있어야 함
START_MONITORING_ON_BOOT = os.getenv("START_MONITORING_ON_BOOT", "true").lower() == "true"
CAMERA_RECONNECT_WAIT_SECONDS = 3

# ── 자동 촬영 (화면이 바뀐 뒤 멈추면 가장 선명한 장면을 찍음) ──
# 이전 화면과 평균 밝기 차이가 이 값보다 크면 "화면이 움직이는 중"
SCENE_CHANGE_THRESHOLD = float(os.getenv("SCENE_CHANGE_THRESHOLD", "6"))
# 화면이 이 시간(초) 동안 멈춰 있으면 촬영
STILL_SECONDS_BEFORE_CAPTURE = float(os.getenv("STILL_SECONDS_BEFORE_CAPTURE", "1.5"))
# 촬영한 사진의 선명도가 이 값보다 낮으면 "판정 불가 (사진 흐림)"
MIN_PHOTO_SHARPNESS = float(os.getenv("MIN_PHOTO_SHARPNESS", "30"))
# 화면 평균 밝기가 이 값보다 어두우면(꺼진 화면, 사진 전환 중) 촬영하지 않음
MIN_PHOTO_BRIGHTNESS = 20
# 실시간 화면의 차량 박스를 다시 계산하는 간격(초). 짧으면 CPU를 많이 씀
LIVE_DETECT_INTERVAL_SECONDS = 0.5

# ── 구역 자동 맞추기 (기준 사진과 특징점 비교) ──
ZONE_MATCH_IMAGE_WIDTH = 1000   # 비교할 때 줄이는 사진 가로 크기 (속도용)
ZONE_MATCH_MIN_INLIERS = 15     # 서로 맞는 특징점이 이 개수 이상이어야 그 구역으로 인정

# ── AI 모델 (팀원 모델 best.pt 를 받으면 models/ 에 넣고 경로만 바꾸면 됨) ──
VEHICLE_MODEL_PATH = os.getenv("VEHICLE_MODEL_PATH", "yolov8n.pt")
VEHICLE_MIN_CONFIDENCE = float(os.getenv("VEHICLE_MIN_CONFIDENCE", "0.4"))
# 번호판 전용 YOLO 모델 (없으면 차량 이미지 전체에서 번호판 글자를 찾음)
PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", os.path.join(PROJECT_DIR, "models", "plate.pt"))
PLATE_MIN_CONFIDENCE = 0.4
# 소방차 전용 YOLO 모델 (없으면 빨간 트럭·버스를 소방차로 판단)
FIRE_TRUCK_MODEL_PATH = os.getenv("FIRE_TRUCK_MODEL_PATH", os.path.join(PROJECT_DIR, "models", "fire_truck.pt"))
FIRE_TRUCK_MIN_CONFIDENCE = 0.5
FIRE_TRUCK_MIN_RED_RATIO = float(os.getenv("FIRE_TRUCK_MIN_RED_RATIO", "0.3"))
# 번호판 OCR이 쓸 CPU 스레드 수 (너무 크면 실시간 화면이 느려짐)
OCR_CPU_THREADS = int(os.getenv("OCR_CPU_THREADS", "2"))

# ── 불법주정차 판정 (1차·2차 촬영 비교) ──
# 1차와 2차 촬영 사이가 이 시간(초) 이상이고 같은 차가 같은 자리에 있으면 단속 (실제 기준 5분, 시연용 10초)
VIOLATION_STAY_SECONDS = float(os.getenv("VIOLATION_STAY_SECONDS", "10"))
# 1차·2차 차량 박스가 이 비율 이상 겹치면 "같은 자리"
SAME_SPOT_MIN_OVERLAP = float(os.getenv("SAME_SPOT_MIN_OVERLAP", "0.5"))
DEFAULT_VIOLATION_TYPE = "소방시설 주정차금지구역"

# ── 저장 경로 ────────────────────────────────────
DATA_DIR = os.path.join(PROJECT_DIR, "data")
PHOTO_DIR = os.path.join(DATA_DIR, "photos")                  # 촬영 원본: photos/2026-10-19/100015_DRONE01_Z01.jpg
DETECTION_IMAGE_DIR = os.path.join(DATA_DIR, "detections")    # 단속 사진(1차+2차): detections/2026-10-19/...
DAILY_RECORD_FILE = os.path.join(DATA_DIR, "daily_records.json")  # 같은 날 덮어쓰기용 기록 (오늘 것만)

# ── 로그 (자동 삭제 없음. 기록 삭제는 관리자만, Boot에서 처리) ──
# logs/server_2026-10-19.log    서버 전체 로그
# logs/violation_2026-10-19.log 위반 기록(고지서 형식) + 판정 불가 기록
LOG_DIR = os.getenv("LOG_DIR", os.path.join(PROJECT_DIR, "logs"))
