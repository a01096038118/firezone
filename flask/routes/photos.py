"""사진 파일 올리기 API (비상용 입구).

카메라 대신 사진 파일(실제 드론 사진 등)을 바로 넣는다. 자동 촬영과 같은 단속 처리로 들어간다.
촬영 시각: 직접 입력(captured_at) → 사진 EXIF 촬영 시각 → 둘 다 없으면 판정 불가 (촬영 시각 없음)
"""
import io
import time

import cv2
import numpy as np
from flask import Blueprint, jsonify, request
from PIL import Image

from camera.camera_config import load_camera_config
from enforcement.enforcement_service import process_photo
from utils.time_format import parse_exif_datetime, parse_input_datetime
from utils.violation_log import write_undecidable

photos_bp = Blueprint("photos", __name__)

SOURCE_UPLOAD = "사진 올리기"
EXIF_TAG_DATETIME_ORIGINAL = 36867   # 실제 촬영 시각
EXIF_TAG_DATETIME = 306              # 파일 수정 시각 (촬영 시각이 없을 때 대신 사용)
EXIF_SUB_IFD = 0x8769                # 촬영 정보가 들어 있는 EXIF 하위 묶음


# 사진 파일의 EXIF 에서 촬영 시각을 읽는 것을 담당함.
def _read_exif_captured_at(image_bytes):
    """timestamp 또는 None (AI로 만든 사진은 보통 없음)."""
    try:
        exif = Image.open(io.BytesIO(image_bytes)).getexif()
    except Exception:
        return None
    # 촬영 시각 → 없으면 파일 시각
    exif_text = exif.get_ifd(EXIF_SUB_IFD).get(EXIF_TAG_DATETIME_ORIGINAL) or exif.get(EXIF_TAG_DATETIME)
    return parse_exif_datetime(exif_text) if exif_text else None


# 요청에서 카메라 ID 를 정하는 것을 담당함.
def _resolve_camera(requested_camera_id):
    cameras = load_camera_config()
    # 지정하지 않으면 첫 번째 카메라(드론)로 봄
    camera_id = requested_camera_id or next(iter(cameras), "UPLOAD")
    return camera_id, cameras.get(camera_id, {}).get("default_zone")


# 사진 파일을 받아 단속 처리하는 API(POST /api/photos)를 담당함.
@photos_bp.route("/photos", methods=["POST"])
def upload_photo():
    """form-data: image(사진 파일, 필수), camera_id(선택), captured_at(선택, "2026-10-19 10:00:00")"""
    # 1. 사진 파일 읽기
    uploaded_file = request.files.get("image")
    if uploaded_file is None:
        return jsonify({"error": "image 파일이 필요합니다."}), 400
    image_bytes = uploaded_file.read()
    photo = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if photo is None:
        return jsonify({"error": "사진을 읽을 수 없습니다."}), 400
    camera_id, default_zone_no = _resolve_camera(request.form.get("camera_id"))

    # 2. 촬영 시각 정하기: 직접 입력 → EXIF → 없으면 판정 불가
    input_time_text = request.form.get("captured_at", "").strip()
    captured_at = parse_input_datetime(input_time_text)
    if input_time_text and captured_at is None:
        return jsonify({"error": "captured_at 형식이 틀렸습니다. 예: 2026-10-19 10:00:00"}), 400
    if captured_at is None:
        captured_at = _read_exif_captured_at(image_bytes)
    if captured_at is None:
        write_undecidable("촬영 시각 없음", camera_id, time.time(), detail="사진에 EXIF 촬영 시각이 없고 직접 입력도 없음")
        return jsonify({"camera_id": camera_id, "status": "판정 불가 (촬영 시각 없음)",
                        "hint": "captured_at 에 촬영 시각을 입력해주세요. 예: 2026-10-19 10:00:00"}), 200

    # 3. 자동 촬영과 같은 단속 처리
    return jsonify(process_photo(camera_id, photo, captured_at, SOURCE_UPLOAD, default_zone_no))
