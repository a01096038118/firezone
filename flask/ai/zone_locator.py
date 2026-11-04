"""팀원 구역 모델(models/fire_zone.pt)로 소방차 전용구역의 대략적인 위치(직사각형)를 찾기.

모델 결과는 똑바른 직사각형이라 그대로 구역으로 쓰면 비스듬한 구역 옆 주차칸까지 들어간다.
그래서 여기서는 "어디쯤 있는지"만 찾고, 정확한 모양은 ai/zone_finder.py(노란 선 규칙)가 그 안에서 찾는다.
모델 파일이 없으면 None 을 돌려줘서, 노란 선 규칙이 사진 전체에서 찾게 한다.
"""
import os
import threading

import numpy as np
from ultralytics import YOLO

import config

# 팀원 모델 클래스 중 구역 전체를 감싸는 클래스 (fire_zone_text 는 바닥 글씨라 쓰지 않음)
ZONE_AREA_CLASS_NAME = "fire_zone_area"

_zone_model = None
# 실시간 화면·사진 분석이 동시에 모델을 쓰지 않도록 잠금
_zone_model_lock = threading.Lock()


# 구역 위치 모델을 처음 한 번만 불러오는 것을 담당함. 모델 파일이 없으면 None.
def _get_zone_model():
    global _zone_model
    if _zone_model is None and os.path.exists(config.FIRE_ZONE_MODEL_PATH):
        _zone_model = YOLO(config.FIRE_ZONE_MODEL_PATH)
    return _zone_model


# 사진에서 구역 위치(가장 확실한 박스 하나)를 넉넉하게 찾는 것을 담당함.
def locate_zone_area(photo):
    """반환: (x1, y1, x2, y2) 사진 픽셀 좌표. 모델 박스보다 FIRE_ZONE_BOX_MARGIN 만큼 넓히고 사진 안으로 자름.
    모델이 없거나 구역을 못 찾으면 None."""
    with _zone_model_lock:
        model = _get_zone_model()
        if model is None:
            return None
        detected_boxes = model.predict(photo, conf=config.FIRE_ZONE_MIN_CONFIDENCE,
                                       imgsz=config.FIRE_ZONE_IMAGE_SIZE, verbose=False)[0].boxes

    best_box, best_confidence = None, 0.0
    for class_id, confidence, corner_coords in zip(detected_boxes.cls.int().tolist(), detected_boxes.conf.tolist(),
                                                   detected_boxes.xyxy.tolist()):
        if model.names[class_id] == ZONE_AREA_CLASS_NAME and confidence > best_confidence:
            best_box, best_confidence = corner_coords, confidence
    if best_box is None:
        return None

    # 박스가 구역 테두리를 살짝 잘라도 노란 선을 찾을 수 있게 넓힘
    photo_height, photo_width = photo.shape[:2]
    x1, y1, x2, y2 = best_box
    margin_x, margin_y = (x2 - x1) * config.FIRE_ZONE_BOX_MARGIN, (y2 - y1) * config.FIRE_ZONE_BOX_MARGIN
    return (int(max(x1 - margin_x, 0)), int(max(y1 - margin_y, 0)),
            int(min(x2 + margin_x, photo_width)), int(min(y2 + margin_y, photo_height)))


# 서버 시작 시 구역 위치 모델을 미리 불러오고 한 번 돌려보는 것(워밍업)을 담당함.
def warmup_zone_model():
    """반환: 모델을 불러왔으면 True, 모델 파일이 없으면 False (노란 선 규칙만 사용)."""
    if not os.path.exists(config.FIRE_ZONE_MODEL_PATH):
        return False
    locate_zone_area(np.zeros((480, 640, 3), dtype=np.uint8))
    return True
