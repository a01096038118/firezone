"""Boot detection_log 에 저장할 데이터 만들기 (Boot DetectionDto 형식)."""
import logging

import config
from utils.image_storage import get_detection_image_url
from utils.time_format import format_boot_datetime

log = logging.getLogger(__name__)

# Boot DetectionEntity 의 VARCHAR 길이 (dl_no 는 Boot가 만드는 번호라 보내지 않음)
DETECTION_LOG_MAX_LENGTH = {
    "dl_camera_id": 20,
    "dl_zone_no": 20,
    "dl_violation_type": 30,
    "dl_car_number": 20,
    "dl_image_path": 255,
}


# DB 컬럼 길이를 넘는 값을 잘라서 저장 오류를 막는 것을 담당함.
def _fit_to_column_length(payload):
    for column, max_length in DETECTION_LOG_MAX_LENGTH.items():
        value = payload.get(column)
        # 비어 있거나 길이 안이면 그대로 둠
        if value is None or len(value) <= max_length:
            continue
        # 사진 주소는 자르면 열리지 않으므로 경고만 남김
        if column == "dl_image_path":
            log.warning("%s 가 DB 길이(%d)를 넘음: %s", column, max_length, value)
            continue
        # 나머지 글자는 DB 길이에 맞게 자름
        log.warning("%s 가 DB 길이(%d)를 넘어 잘라서 보냄: %s", column, max_length, value)
        payload[column] = value[:max_length]
    return payload


# Boot detection_log 형식(dl_*)의 전송 데이터를 만드는 것을 담당함.
def build_detection_payload(camera_id, zone_no, violation_type, car_number,
                            evidence_image_path, first_detected_at, last_detected_at):
    """Boot는 7개 칸이 모두 필수(NOT NULL). 단속은 차량번호를 읽은 경우에만 되므로 항상 채워진다.
    사진을 Boot에 파일로 넘기는 방식(config.BOOT_IMAGE_UPLOAD)이면 dl_image_path 는 Boot가 채우므로 보내지 않는다."""
    payload = {
        "dl_camera_id": camera_id,
        "dl_zone_no": zone_no,
        "dl_violation_type": violation_type,
        "dl_car_number": car_number,
        "dl_image_path": get_detection_image_url(evidence_image_path),   # 1차+2차 단속 사진 전체 주소
        "dl_first_detected_at": format_boot_datetime(first_detected_at),  # 1차 촬영 시각
        "dl_last_detected_at": format_boot_datetime(last_detected_at),    # 2차(마지막) 촬영 시각
    }
    if config.BOOT_IMAGE_UPLOAD:
        del payload["dl_image_path"]
    return _fit_to_column_length(payload)
