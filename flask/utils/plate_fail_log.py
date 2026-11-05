"""번호판 미인식 분석 기록 (Flask에만 남김. Boot·DB로는 보내지 않음).

구역 안에 차가 있는데 번호판을 못 읽은 경우, 나중에 사람이 확인하고 모델을 개선할 수 있게 남긴다.

logs/plate_fail_2026-10-19.log 예시 (한 줄에 차량 한 대)
    10:00:15 DRONE01 / 구역 AUTO / 차량 2 | 원인: 번호판 형식 불일치 | OCR 원본: "35079487" (점수 0.95) | 번호판 YOLO 0.83 | 사진: data/plate_failures/2026-10-19/100015_DRONE01_AUTO_car2_vehicle.jpg

data/plate_failures/2026-10-19/
    100015_DRONE01_AUTO_car2_vehicle.jpg   차량 사진
    100015_DRONE01_AUTO_car2_plate.jpg     OCR에 넣은 번호판 사진 (번호판을 찾은 경우만)
"""
import logging
import os
from datetime import datetime

import cv2

import config

PLATE_FAIL_LOGGER_NAME = "plate_fail"
plate_fail_logger = logging.getLogger(PLATE_FAIL_LOGGER_NAME)
log = logging.getLogger(__name__)


# 차량·번호판 사진을 날짜 폴더에 저장하는 것을 담당함.
def _save_failure_images(camera_id, zone_no, captured_at, car_index, vehicle_image, plate_image):
    """반환: 차량 사진의 data/ 기준 경로 (저장 안 했으면 None)."""
    taken_at = datetime.fromtimestamp(captured_at)
    date_folder = f"{taken_at:%Y-%m-%d}"
    os.makedirs(os.path.join(config.PLATE_FAIL_IMAGE_DIR, date_folder), exist_ok=True)
    base_name = f"{taken_at:%H%M%S}_{camera_id}_{zone_no or 'NOZONE'}_car{car_index}"
    # 같은 초·같은 차 번호면 _2, _3 을 붙임
    same_name_count = 1
    while os.path.exists(os.path.join(config.PLATE_FAIL_IMAGE_DIR, date_folder, f"{base_name}_vehicle.jpg")):
        same_name_count += 1
        base_name = f"{taken_at:%H%M%S}_{camera_id}_{zone_no or 'NOZONE'}_car{car_index}_{same_name_count}"

    vehicle_path = os.path.join(date_folder, f"{base_name}_vehicle.jpg")
    cv2.imwrite(os.path.join(config.PLATE_FAIL_IMAGE_DIR, vehicle_path), vehicle_image)
    if plate_image is not None and plate_image.size > 0:
        cv2.imwrite(os.path.join(config.PLATE_FAIL_IMAGE_DIR, date_folder, f"{base_name}_plate.jpg"), plate_image)
    return f"data/plate_failures/{vehicle_path.replace(os.sep, '/')}"


# 구역 안 차량의 번호판을 못 읽었을 때 원인·OCR 원본·사진을 남기는 것을 담당함.
def write_plate_failure(camera_id, zone_no, captured_at, car_index, vehicle_box, vehicle_image, plate_detail):
    """plate_detail: ai.plate.readLicensePlateDetail 결과. 기록에 실패해도 단속 흐름은 멈추지 않는다."""
    if not config.PLATE_FAIL_LOG_ENABLED:
        return
    try:
        image_path = None
        if config.PLATE_FAIL_SAVE_IMAGES and vehicle_image is not None and vehicle_image.size > 0:
            image_path = _save_failure_images(camera_id, zone_no, captured_at, car_index,
                                              vehicle_image, plate_detail.get("plate_image"))

        parts = [f"{datetime.fromtimestamp(captured_at):%H:%M:%S} {camera_id} / 구역 {zone_no} / 차량 {car_index} {tuple(vehicle_box)}",
                 f"원인: {plate_detail.get('fail_reason')}"]
        if plate_detail.get("ocr_text"):
            scores = ", ".join(f"{score:.2f}" for score in plate_detail.get("ocr_scores", []))
            parts.append(f'OCR 원본: "{plate_detail["ocr_text"]}" (점수 {scores or "-"})')
        if plate_detail.get("plate_confidence") is not None:
            parts.append(f"번호판 YOLO {plate_detail['plate_confidence']:.2f}")
        elif not plate_detail.get("used_plate_model"):
            parts.append("번호판 모델 없음 (차량 전체로 OCR)")
        if image_path:
            parts.append(f"사진: {image_path}")
        plate_fail_logger.info(" | ".join(parts))
    except Exception:
        log.exception("번호판 미인식 기록 실패 (단속은 계속 진행)")
