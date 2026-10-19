"""차량 탐지 (MON-002).

클래스를 번호가 아니라 이름으로 구분해서, 팀원이 학습시킨 모델(best.pt)로 바꿔도 코드를 고치지 않는다.
- 기본 모델(yolov8n.pt): car, motorcycle, bus, truck
- 팀원 모델: car, vehicle, suv ... 처럼 이름이 달라도 아래 목록에 넣으면 됨
- 팀원 모델에 fire_truck 클래스가 있으면 소방차로 바로 표시함
"""
import threading

import numpy as np
from ultralytics import YOLO

import config

# 모델 클래스 이름 → 차량 종류. 여기에 있는 이름만 차량으로 본다.
VEHICLE_TYPE_BY_CLASS_NAME = {
    "car": "car", "vehicle": "car", "suv": "car", "van": "car", "taxi": "car",
    "truck": "truck", "bus": "bus", "motorcycle": "motorcycle", "motorbike": "motorcycle",
    "fire_truck": "fire_truck", "firetruck": "fire_truck", "fire truck": "fire_truck",
}

_vehicle_model = None
# 같은 모델을 여러 스레드(실시간 화면, 사진 분석)가 동시에 쓰지 않도록 잠금
_vehicle_model_lock = threading.Lock()


# 차량 탐지 모델을 처음 한 번만 불러오는 것을 담당함.
def _get_vehicle_model():
    global _vehicle_model
    if _vehicle_model is None:
        _vehicle_model = YOLO(config.VEHICLE_MODEL_PATH)
    return _vehicle_model


# 모델 클래스 번호 중 차량에 해당하는 번호만 고르는 것을 담당함.
def _vehicle_class_ids(model):
    # 모델이 아는 클래스 이름 중 차량 목록에 있는 것만 골라 번호를 돌려줌
    return [class_id for class_id, class_name in model.names.items()
            if class_name.lower() in VEHICLE_TYPE_BY_CLASS_NAME]


# 사진에서 차량을 찾고 위치(박스)를 돌려주는 것을 담당함.
def detectVehicle(image):
    """사진에서 차량을 찾는다.

    반환: [{"vehicle_type": "car", "confidence": 0.91, "box": (x1, y1, x2, y2)}, ...]
          box 는 차량 박스의 왼쪽 위(x1, y1), 오른쪽 아래(x2, y2) 픽셀 좌표
    모델 실행에 실패하면 예외를 그대로 올린다 (호출한 쪽에서 "탐지 실패" 로 기록).
    """
    with _vehicle_model_lock:
        model = _get_vehicle_model()
        # 차량 클래스만, 기준 신뢰도 이상인 것만 찾음
        detected_boxes = model.predict(
            image, classes=_vehicle_class_ids(model),
            conf=config.VEHICLE_MIN_CONFIDENCE, verbose=False,
        )[0].boxes
        class_names = model.names

    # 아무것도 못 찾았으면 빈 목록
    if detected_boxes is None or len(detected_boxes) == 0:
        return []

    # 모델 결과를 다루기 쉬운 dict 목록으로 바꿈
    vehicles = []
    for class_id, confidence, corner_coords in zip(
        detected_boxes.cls.int().tolist(),
        detected_boxes.conf.tolist(),
        detected_boxes.xyxy.tolist(),
    ):
        vehicles.append({
            "vehicle_type": VEHICLE_TYPE_BY_CLASS_NAME[class_names[class_id].lower()],
            "confidence": round(confidence, 3),
            "box": tuple(int(coord) for coord in corner_coords),
        })
    return vehicles


# 서버 시작 시 차량 탐지 모델을 미리 불러오고 한 번 돌려보는 것(워밍업)을 담당함.
def warmup_vehicle_model():
    """첫 사진 분석이 모델 로딩 때문에 늦어지는 것을 막는다."""
    # 빈 화면을 한 번 분석해서 모델을 메모리에 올려둠
    detectVehicle(np.zeros((480, 640, 3), dtype=np.uint8))
