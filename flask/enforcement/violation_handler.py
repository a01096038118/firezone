"""위반 확정 처리: 같은 날 기록 확인 → 단속 사진 저장 → 위반 로그 → Boot 전송."""
import logging

import config
from boot.payload import build_detection_payload
from boot.sender import sendDetection, sendDetectionWithImage, updateDetection
from enforcement.daily_records import find_record, make_record_key, make_record_number, save_record
from enforcement.evidence_image import build_evidence_image
from utils.image_storage import get_detection_image_url, save_detection_image
from utils.violation_log import ACTION_NEW_RECORD, ACTION_OVERWRITE, write_violation_record

log = logging.getLogger(__name__)


# 위반이 확정된 차량 한 대를 기록하고 Boot에 보내는 것을 담당함.
def handle_violation(second_shot, judgment):
    """반환: 화면·API에 보여줄 위반 정보 dict"""
    car_number = judgment.car.car_number
    camera_id, zone_no = second_shot.camera_id, second_shot.zone_no
    first_sighting = judgment.first_sighting

    # 1. 같은 날 같은 차의 기록이 있는지 확인 (있으면 덮어쓰기)
    record_key = make_record_key(camera_id, zone_no, car_number, second_shot.captured_at)
    existing_record = find_record(record_key)
    is_new_record = existing_record is None
    # 최초 탐지 시간은 그날 처음 단속된 기록의 시간을 유지
    first_detected_at = (first_sighting.shot.captured_at if is_new_record
                         else existing_record["first_detected_at"])
    last_detected_at = second_shot.captured_at

    # 2. 1차·2차 사진을 붙인 단속 사진 저장
    evidence_image = build_evidence_image(first_sighting, second_shot, judgment.car)
    evidence_image_path = save_detection_image(camera_id, zone_no, evidence_image, last_detected_at)

    # 3. 같은 날 기록 저장 (새로 만들거나 덮어씀)
    record_number = make_record_number(camera_id, zone_no, car_number, first_detected_at)
    save_record(record_key, {
        "record_number": record_number,
        "first_detected_at": first_detected_at,
        "last_detected_at": last_detected_at,
        "image_path": evidence_image_path,
    })

    # 4. 고지서 형식 위반 로그
    write_violation_record(
        record_number, ACTION_NEW_RECORD if is_new_record else ACTION_OVERWRITE,
        camera_id, zone_no, second_shot.zone_name, car_number,
        first_detected_at, last_detected_at, evidence_image_path,
    )

    # 5. Boot 전송
    payload = build_detection_payload(camera_id, zone_no, second_shot.violation_type, car_number,
                                      evidence_image_path, first_detected_at, last_detected_at)
    # 사진을 Boot에 넘기는 방식: 매번 사진과 함께 저장 요청 (같은 날이면 Boot가 갱신, 보낸 사진은 Flask에서 지움)
    if config.BOOT_IMAGE_UPLOAD:
        sendDetectionWithImage(record_key, payload, evidence_image_path)
    # 새 기록은 저장, 같은 날 재단속은 수정
    elif is_new_record:
        sendDetection(record_key, payload)
    else:
        updateDetection(record_key, payload)

    return {
        "record_number": record_number,
        "is_new_record": is_new_record,
        "car_number": car_number,
        "box": [int(value) for value in judgment.car.box],   # 실시간 화면에 빨간 테두리로 표시할 위치 (2차 사진 기준)
        "first_detected_at": first_detected_at,
        "last_detected_at": last_detected_at,
        "evidence_image_url": get_detection_image_url(evidence_image_path),
    }
