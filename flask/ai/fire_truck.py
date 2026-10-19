"""소방차 구별: 소방차는 금지구역에 있어도 위반이 아니다. 소방차가 아닌 차량은 전부 단속 대상.

판단 순서
  1) 차량 탐지 모델이 fire_truck 클래스로 찾았으면 소방차 (팀원 모델에 클래스가 있을 때)
  2) 소방차 전용 모델(models/fire_truck.pt)이 있으면 그 모델로 판단
  3) 둘 다 없으면 트럭·버스 중 차체가 대부분 빨간색인 차량을 소방차로 봄
"""
import os
import threading

import cv2
from ultralytics import YOLO

import config

# 빨간색 판단으로 소방차 후보가 될 수 있는 차량 종류 (승용차·오토바이는 소방차가 아님)
FIRE_TRUCK_CANDIDATE_TYPES = {"truck", "bus"}

_fire_truck_model = None
_fire_truck_model_lock = threading.Lock()


# 소방차 전용 모델을 처음 한 번만 불러오는 것을 담당함. 모델 파일이 없으면 None.
def _get_fire_truck_model():
    global _fire_truck_model
    if _fire_truck_model is None and os.path.exists(config.FIRE_TRUCK_MODEL_PATH):
        _fire_truck_model = YOLO(config.FIRE_TRUCK_MODEL_PATH)
    return _fire_truck_model


# 차량 이미지에서 빨간색이 차지하는 비율을 계산하는 것을 담당함.
def _red_color_ratio(vehicle_image):
    hsv_image = cv2.cvtColor(vehicle_image, cv2.COLOR_BGR2HSV)
    # 빨간색은 색상(H) 값이 0 근처와 180 근처 양쪽에 걸쳐 있어서 두 범위를 합침
    low_red = cv2.inRange(hsv_image, (0, 100, 70), (10, 255, 255))
    high_red = cv2.inRange(hsv_image, (170, 100, 70), (180, 255, 255))
    red_pixel_count = cv2.countNonZero(low_red) + cv2.countNonZero(high_red)
    return red_pixel_count / (vehicle_image.shape[0] * vehicle_image.shape[1])


# 차량 한 대가 소방차인지 판단하는 것을 담당함.
def isFireTruck(vehicle_image, vehicle_type):
    # 차량 탐지 모델이 이미 소방차로 분류했으면 바로 소방차
    if vehicle_type == "fire_truck":
        return True
    if vehicle_image is None or vehicle_image.size == 0:
        return False

    # 소방차 전용 모델이 있으면 그 모델로 판단
    fire_truck_model = _get_fire_truck_model()
    if fire_truck_model is not None:
        with _fire_truck_model_lock:
            found_boxes = fire_truck_model.predict(
                vehicle_image, conf=config.FIRE_TRUCK_MIN_CONFIDENCE, verbose=False,
            )[0].boxes
        return found_boxes is not None and len(found_boxes) > 0

    # 전용 모델이 없으면 빨간 트럭·버스를 소방차로 봄
    if vehicle_type not in FIRE_TRUCK_CANDIDATE_TYPES:
        return False
    return _red_color_ratio(vehicle_image) >= config.FIRE_TRUCK_MIN_RED_RATIO


# 사진 속 차량마다 소방차인지 표시(vehicle["is_fire_truck"])하는 것을 담당함.
def mark_fire_trucks(image, vehicles):
    for vehicle in vehicles:
        # 차량 부분만 잘라서 판단함
        x1, y1, x2, y2 = vehicle["box"]
        vehicle["is_fire_truck"] = isFireTruck(image[max(y1, 0):y2, max(x1, 0):x2], vehicle["vehicle_type"])
