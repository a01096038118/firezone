"""카메라·드론 목록(config.CAMERAS)과 구역 목록(zones/zones.json) 읽기."""
import json
import os

import cv2

import config

# 기준 사진 경로 → (가로, 세로). 기준 사진 크기는 바뀌지 않으므로 한 번만 읽음
_reference_size_by_path = {}


# 카메라(드론) 목록을 돌려주는 것을 담당함.
def load_camera_config():
    """{카메라 ID: {"name", "enabled", "source", "default_zone"}} (config.CAMERAS)"""
    return config.CAMERAS


# 기준 사진의 크기를 읽는 것을 담당함.
def _read_reference_size(reference_image):
    if reference_image not in _reference_size_by_path:
        image = cv2.imread(os.path.join(config.PROJECT_DIR, reference_image))
        # 사진이 없으면 None (구역 맞추기에서 그 구역을 건너뜀)
        _reference_size_by_path[reference_image] = (image.shape[1], image.shape[0]) if image is not None else None
    return _reference_size_by_path[reference_image]


# zones/zones.json 파일 읽기를 담당함.
def load_zones():
    """[{"zone_no", "name", "violation_type", "reference_image", "polygon", "reference_size"}, ...]
    기준 사진이 없는 구역은 빠진다."""
    # 구역 파일이 아직 없으면 빈 목록
    if not os.path.exists(config.ZONE_CONFIG_FILE):
        return []
    with open(config.ZONE_CONFIG_FILE, encoding="utf-8") as zone_file:
        zones_by_no = json.load(zone_file)

    zones = []
    for zone_no, zone in zones_by_no.items():
        # 기준 사진 크기를 붙여서 돌려줌 (구역 테두리 비율 → 픽셀 계산에 필요)
        reference_size = _read_reference_size(zone["reference_image"])
        if reference_size is None:
            continue
        zones.append({
            "zone_no": zone_no,
            "name": zone.get("name", zone_no),
            "violation_type": zone.get("violation_type", config.DEFAULT_VIOLATION_TYPE),
            "reference_image": zone["reference_image"],
            "polygon": zone["polygon"],
            "reference_size": reference_size,
        })
    return zones


# 카메라 주소가 웹캠 번호/스트림 주소/영상 파일 중 무엇인지 구분하는 것을 담당함.
def parse_video_source(source):
    """반환: (OpenCV에 넘길 값, 영상 파일 여부)
    "0" → 웹캠 번호 / "http://..." → ESP32-CAM 스트림 / 그 외 → 영상 파일 경로(프로젝트 기준)"""
    # 숫자면 PC에 연결된 카메라 번호
    if isinstance(source, int) or str(source).isdigit():
        return int(source), False
    # 주소면 ESP32-CAM 같은 네트워크 스트림
    if "://" in str(source):
        return source, False
    # 나머지는 영상 파일 (시연·테스트용)
    file_path = source if os.path.isabs(source) else os.path.join(config.PROJECT_DIR, source)
    return file_path, True
