"""사진 저장과 접근 주소.

data/photos/2026-10-19/100015_DRONE01_Z01.jpg       촬영 원본 (1차·2차 모두)
data/detections/2026-10-19/100015_DRONE01_Z01.jpg   단속 사진 (1차+2차를 붙인 사진, Boot에 보내는 사진)
"""
import os
from datetime import datetime

import cv2

import config


# 날짜 폴더에 같은 이름이 없도록 사진 경로를 정하는 것을 담당함.
def _make_unique_path(base_dir, camera_id, zone_no, timestamp):
    """base_dir 기준 상대 경로를 돌려준다. 예: 2026-10-19/100015_DRONE01_Z01.jpg"""
    taken_at = datetime.fromtimestamp(timestamp)
    date_folder = f"{taken_at:%Y-%m-%d}"
    # 날짜 폴더가 없으면 만듦
    os.makedirs(os.path.join(base_dir, date_folder), exist_ok=True)

    base_name = f"{taken_at:%H%M%S}_{camera_id}_{zone_no or 'NOZONE'}"
    relative_path = f"{date_folder}/{base_name}.jpg"
    # 같은 초에 두 장이면 _2, _3 을 붙임
    same_name_count = 1
    while os.path.exists(os.path.join(base_dir, relative_path)):
        same_name_count += 1
        relative_path = f"{date_folder}/{base_name}_{same_name_count}.jpg"
    return relative_path


# 촬영 원본 사진을 저장하는 것을 담당함.
def save_photo(camera_id, zone_no, image, timestamp):
    """data/photos 기준 상대 경로를 돌려준다."""
    relative_path = _make_unique_path(config.PHOTO_DIR, camera_id, zone_no, timestamp)
    cv2.imwrite(os.path.join(config.PHOTO_DIR, relative_path), image)
    return relative_path


# 단속 사진(1차+2차)을 저장하는 것을 담당함.
def save_detection_image(camera_id, zone_no, image, timestamp):
    """data/detections 기준 상대 경로를 돌려준다."""
    relative_path = _make_unique_path(config.DETECTION_IMAGE_DIR, camera_id, zone_no, timestamp)
    cv2.imwrite(os.path.join(config.DETECTION_IMAGE_DIR, relative_path), image)
    return relative_path


# 단속 사진을 볼 수 있는 Flask 주소를 만드는 것을 담당함.
def get_detection_image_url(relative_path):
    """Boot·화면에서 <img src> 로 바로 쓰는 전체 주소 (routes/images.py 가 제공)."""
    if not relative_path:
        return None
    return f"{config.FLASK_PUBLIC_URL}/api/images/detections/{relative_path}"


# 촬영 원본 사진을 볼 수 있는 Flask 주소를 만드는 것을 담당함.
def get_photo_url(relative_path):
    if not relative_path:
        return None
    return f"{config.FLASK_PUBLIC_URL}/api/images/photos/{relative_path}"
