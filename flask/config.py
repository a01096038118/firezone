"""Flask AI 서버 설정. 대부분 환경변수로 바꿀 수 있다."""
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Flask 서버 ───────────────────────────────────
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
# Boot·브라우저가 사진·영상에 접근할 Flask 주소 (dev 서버 107, prod 서버 108 → prod는 환경변수로 지정)
FLASK_PUBLIC_URL = os.getenv("FLASK_PUBLIC_URL", "http://192.168.0.141:5000")

# ── Boot 연동 (Boot 관리자 앱 firezonePjt_admin 기준) ──
# false 이면 Boot로 보내지 않고 보낼 내용만 로그로 출력 (Boot 없이 테스트용)
BOOT_ENABLED = os.getenv("BOOT_ENABLED", "true").lower() == "true"
# Boot 관리자 서버 주소 (dev 서버 103, prod 서버 104 → prod는 환경변수로 지정)
BOOT_URL = os.getenv("BOOT_URL", "http://192.168.56.103:8090")
BOOT_DETECTION_API_PATH = os.getenv("BOOT_DETECTION_API_PATH", "/detections")
BOOT_REQUEST_TIMEOUT_SECONDS = float(os.getenv("BOOT_REQUEST_TIMEOUT_SECONDS", "3"))
# Boot에 수정 API(PUT /detections/{dl_no})가 생기면 true
BOOT_UPDATE_API_READY = os.getenv("BOOT_UPDATE_API_READY", "false").lower() == "true"
# Boot가 단속 사진 파일을 함께 받아 저장하면(multipart: detection + image) true
#   true 이면: 위반할 때마다 POST 로 사진과 함께 보냄 (Boot가 같은 날 기록이면 갱신)
#             Boot 저장에 성공한 단속 사진과 촬영 원본은 Flask에 남기지 않음 (사진 원본은 Boot에만)
BOOT_IMAGE_UPLOAD = os.getenv("BOOT_IMAGE_UPLOAD", "true").lower() == "true"
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
        "source": os.getenv("DRONE01_SOURCE", "http://192.168.0.59:81/stream"),
        # 자동으로 찾은 구역의 구역번호를 이 카메라만 직접 정함 (영상 표 VIDEO_ZONE_NO 보다 먼저). 없으면 None
        "zone_no": os.getenv("DRONE01_ZONE_NO") or None,
        # 등록된 구역 사진과 맞지 않을 때 쓸 고정 구역. None 이면 판정 불가 (다른 아파트를 찍었을 때 잘못 단속하지 않게)
        "default_zone": None,
    },
    # Boot 관제 화면의 CAM_01 버튼 = Flask PC에 꽂은 웹캠(Osmo Pocket 등). 웹캠 번호는 PC마다 다를 수 있음 (CAM01_SOURCE 로 바꿈)
    "CAM_01": {
        "name": "웹캠 1",
        "enabled": os.getenv("CAM01_ENABLED", "true").lower() == "true",
        "source": os.getenv("CAM01_SOURCE", "1"),
        "zone_no": os.getenv("CAM01_ZONE_NO") or None,
        "default_zone": None,
    },
}
# 웹캠으로 받을 화면 크기 (웹캠이 지원하지 않으면 가장 가까운 크기로 받음)
WEBCAM_WIDTH = int(os.getenv("WEBCAM_WIDTH", "1920"))
WEBCAM_HEIGHT = int(os.getenv("WEBCAM_HEIGHT", "1080"))
# 웹캠이 이 밝기(0~255) 미만의 검은 화면을 이 시간(초) 동안 계속 보내면 끊고 다시 연결함
WEBCAM_BLACK_MAX_BRIGHTNESS = 3
WEBCAM_BLACK_RECONNECT_SECONDS = 5
ZONE_CONFIG_FILE = os.path.join(PROJECT_DIR, "zones", "zones.json")   # 구역 목록 (기준 사진 + 구역 테두리)
# 등록된 구역 사진과 맞지 않으면 바닥 표시(노란 테두리 직선 4개)로 구역을 직접 찾음
AUTO_ZONE_ENABLED = os.getenv("AUTO_ZONE_ENABLED", "true").lower() == "true"
AUTO_ZONE_NO = os.getenv("AUTO_ZONE_NO", "AUTO")          # 자동으로 찾은 구역의 구역번호 (Boot dl_zone_no)
# 시연용: 카메라 입력이 영상 파일이면 파일 이름으로 구역번호를 정함 (표에 없는 영상·실제 드론은 AUTO_ZONE_NO)
#   파일 이름은 대소문자·확장자까지 똑같이 적어야 함. 값은 Boot dl_zone_no 로 그대로 감 (최대 20자)
VIDEO_ZONE_NO = {
    "133V.MP4": "1",     # 시연 영상 1 (4K 원본) → 구역 1
    "133V_1.mp4": "1",   # 같은 장면의 1080p 영상 → 구역 1
    "133V_1.avi": "1",   # 시연용: 4K 원본의 같은 구간(5.6~42.9초)을 3200x1800·초당 30장으로 만든 영상
    "152V.MP4": "2",     # 시연 영상 2 (4K 원본) → 구역 2
    "152V_1.avi": "2",   # 시연용: 4K 원본을 3200x1800·초당 30장으로 줄인 영상 (번호판 인식이 4K와 같고 화면도 부드러움)
}
AUTO_ZONE_MIN_AREA_RATIO = 0.03                           # 구역이 사진에서 최소 이 비율 이상 커야 함
AUTO_ZONE_MAX_PAINT_RATIO = 0.15                          # 구역 안이 이 비율 넘게 노랗게 칠해져 있으면 횡단보도·벽으로 보고 제외
AUTO_ZONE_MIN_OUTLINE_COVERAGE = 0.6                      # 구역 네 변을 따라 평균 이 비율 이상 노란 선이 그려져 있어야 함
# 팀원 구역 모델(fire_zone_area 박스)로 구역 "위치"를 먼저 찾고, 그 안에서만 노란 선을 찾음 (없으면 사진 전체에서 찾음)
#   모델 박스는 직사각형이라 그대로 쓰면 옆 주차칸까지 들어감 → 위치만 쓰고 모양은 노란 선으로 잡음 (11/4 비교: 오탐지 0)
FIRE_ZONE_MODEL_PATH = os.getenv("FIRE_ZONE_MODEL_PATH", os.path.join(PROJECT_DIR, "models", "fire_zone.pt"))
FIRE_ZONE_MIN_CONFIDENCE = float(os.getenv("FIRE_ZONE_MIN_CONFIDENCE", "0.4"))
FIRE_ZONE_IMAGE_SIZE = 640       # 팀원 모델 학습 입력 크기
FIRE_ZONE_BOX_MARGIN = 0.15      # 모델 박스보다 이 비율만큼 넓게 봄 (박스가 테두리를 살짝 잘라도 찾게)
START_MONITORING_ON_BOOT = os.getenv("START_MONITORING_ON_BOOT", "true").lower() == "true"
CAMERA_RECONNECT_WAIT_SECONDS = 3

# ── 자동 촬영 (화면이 바뀐 뒤 멈추면 가장 선명한 장면을 찍음) ──
# 이전 화면과 평균 밝기 차이가 이 값보다 크면 "화면이 움직이는 중"
SCENE_CHANGE_THRESHOLD = float(os.getenv("SCENE_CHANGE_THRESHOLD", "6"))
# 화면이 이 시간(초) 동안 멈춰 있으면 촬영
STILL_SECONDS_BEFORE_CAPTURE = float(os.getenv("STILL_SECONDS_BEFORE_CAPTURE", "1.5"))
# 찍은 뒤에도 화면이 그대로면 이 시간(초)마다 다시 찍음 (드론이 떠 있기만 해도 2차 촬영). 0 이면 다시 찍지 않음
#   위반 판정 시간(VIOLATION_STAY_SECONDS)과 같게 두면 호버링 시작 후 그 시간이 지나자마자 2차 촬영이 됨
STILL_RECAPTURE_SECONDS = float(os.getenv("STILL_RECAPTURE_SECONDS", "10"))
# 촬영한 사진의 선명도가 이 값보다 낮으면 "판정 불가 (사진 흐림)"
MIN_PHOTO_SHARPNESS = float(os.getenv("MIN_PHOTO_SHARPNESS", "30"))
# 화면 평균 밝기가 이 값보다 어두우면(꺼진 화면, 사진 전환 중) 촬영하지 않음
MIN_PHOTO_BRIGHTNESS = 20
# 실시간 화면의 차량 박스를 다시 계산하는 간격(초). 짧으면 CPU를 많이 씀
LIVE_DETECT_INTERVAL_SECONDS = 0.5
# 실시간 화면(박스 그리기·JPEG 전송) 가로 크기. 4K 영상도 이 크기로 줄여 그려서 화면이 느려지지 않게 함
#   번호판 인식·판정에 쓰는 자동 촬영 사진은 원본 크기(4K) 그대로. 0 이면 줄이지 않음
LIVE_VIEW_WIDTH = int(os.getenv("LIVE_VIEW_WIDTH", "1280"))
# 드론이 움직이는 중에도 구역을 보여주려고 이 간격(초)마다 화면 표시용 구역을 찾음 (판정에는 안 씀). 0 이면 끔
LIVE_ZONE_INTERVAL_SECONDS = float(os.getenv("LIVE_ZONE_INTERVAL_SECONDS", "0.5"))
# 화면 표시용 구역은 찾은 뒤 이 시간(초)까지만 그림 (오래되면 드론이 움직여 위치가 안 맞음)
LIVE_ZONE_MAX_AGE_SECONDS = 1.0
# 흔들림 줄이기: 새 구역 꼭짓점이 직전보다 화면 가로의 이 비율 안에서 움직였으면 직전과 섞어서 부드럽게 옮김
LIVE_ZONE_SMOOTH_MAX_MOVE_RATIO = 0.08
LIVE_ZONE_SMOOTH_NEW_WEIGHT = 0.5      # 섞을 때 새 위치 비중 (작을수록 덜 흔들리지만 늦게 따라감)
# 실시간 화면에서 구역 안을 노란색으로 반투명하게 칠하는 진하기 (0 이면 칠하지 않음, 1 이면 꽉 채움)
ZONE_FILL_OPACITY = float(os.getenv("ZONE_FILL_OPACITY", "0.25"))

# ── 구역 자동 맞추기 (기준 사진과 특징점 비교) ──
ZONE_MATCH_IMAGE_WIDTH = 1000   # 비교할 때 줄이는 사진 가로 크기 (속도용)
ZONE_MATCH_MIN_INLIERS = 15     # 서로 맞는 특징점이 이 개수 이상이어야 그 구역으로 인정

# ── AI 모델 (팀원 모델 best.pt 를 받으면 models/ 에 넣고 경로만 바꾸면 됨) ──
VEHICLE_MODEL_PATH = os.getenv("VEHICLE_MODEL_PATH", "yolov8n.pt")
# 위에서 내려다본 흰 차를 0.4 근처로 겨우 잡는 경우가 있어 0.3 사용 (11/4: 0.4에서 10/23 위반 차량을 놓침)
VEHICLE_MIN_CONFIDENCE = float(os.getenv("VEHICLE_MIN_CONFIDENCE", "0.3"))
# 두 차량 박스가 이 비율(IoU) 이상 겹치면 같은 차로 보고 하나만 남김 (종류가 car·truck 으로 달라도)
VEHICLE_MERGE_IOU = float(os.getenv("VEHICLE_MERGE_IOU", "0.7"))
# 번호판 전용 YOLO 모델 (없으면 차량 이미지 전체에서 번호판 글자를 찾음)
# 팀원 모델: YOLO11n 기반, 클래스 License_Plate 하나 (pjt_best/flask_handoff/README.txt 기준값)
PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", os.path.join(PROJECT_DIR, "models", "plate.pt"))
PLATE_MIN_CONFIDENCE = float(os.getenv("PLATE_MIN_CONFIDENCE", "0.4"))
PLATE_IMAGE_SIZE = int(os.getenv("PLATE_IMAGE_SIZE", "960"))   # 학습할 때 쓴 입력 크기
PLATE_IOU = float(os.getenv("PLATE_IOU", "0.45"))               # 겹친 번호판 박스를 하나로 합치는 기준
# 소방차 전용 YOLO 모델 (없으면 빨간 트럭·버스를 소방차로 판단)
FIRE_TRUCK_MODEL_PATH = os.getenv("FIRE_TRUCK_MODEL_PATH", os.path.join(PROJECT_DIR, "models", "fire_truck.pt"))
FIRE_TRUCK_MIN_CONFIDENCE = 0.5
FIRE_TRUCK_MIN_RED_RATIO = float(os.getenv("FIRE_TRUCK_MIN_RED_RATIO", "0.3"))
# 소방차 모델이 없을 때: 같은 사진 속 차량 크기 중앙값보다 이 배수 이상 큰 빨간 차만 소방차로 봄
#   (차 종류를 car 로 통일해서 트럭·버스 구분 대신 크기로 큰 차를 고름. 빨간 승용차가 소방차로 빠지지 않게)
FIRE_TRUCK_MIN_SIZE_RATIO = float(os.getenv("FIRE_TRUCK_MIN_SIZE_RATIO", "2.0"))
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
# 번호판 미인식 분석 (Flask에만 남김. Boot·DB로는 보내지 않음)
#   구역 안 차량의 번호판을 못 읽으면 logs/plate_fail_날짜.log 에 원인·OCR 원본을 남기고,
#   PLATE_FAIL_SAVE_IMAGES 이면 data/plate_failures/날짜/ 에 차량·번호판 사진도 저장 (나중에 사람이 확인·모델 개선용)
PLATE_FAIL_LOG_ENABLED = os.getenv("PLATE_FAIL_LOG_ENABLED", "true").lower() == "true"
PLATE_FAIL_SAVE_IMAGES = os.getenv("PLATE_FAIL_SAVE_IMAGES", "true").lower() == "true"
PLATE_FAIL_IMAGE_DIR = os.path.join(DATA_DIR, "plate_failures")

# ── 로그 (자동 삭제 없음. 기록 삭제는 관리자만, Boot에서 처리) ──
# logs/server_2026-10-19.log    서버 전체 로그
# logs/violation_2026-10-19.log 위반 기록(고지서 형식) + 판정 불가 기록
# logs/plate_fail_2026-10-19.log 번호판 미인식 분석 기록 (구역 안 차량만)
LOG_DIR = os.getenv("LOG_DIR", os.path.join(PROJECT_DIR, "logs"))
