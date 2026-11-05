"""소방차 구별: 소방차는 금지구역에 있어도 위반이 아니다. 소방차가 아닌 차량은 전부 단속 대상.

판단 순서
  1) 차량 탐지 모델이 fire_truck 클래스로 찾았으면 소방차 (팀원 모델에 클래스가 있을 때)
  2) 소방차 전용 모델(models/fire_truck.pt)이 있으면 그 모델로 판단
  3) 둘 다 없으면 같은 사진의 다른 차보다 확실히 큰(FIRE_TRUCK_MIN_SIZE_RATIO 배 이상) 차 중
     차체가 대부분 빨간색인 차량을 소방차로 봄 (차 종류는 모두 car 로 통일해서 크기로 큰 차를 구분)
"""
import os
import threading

import cv2
import numpy as np
from ultralytics import YOLO

import config

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
def isFireTruck(vehicle_image, vehicle_type, is_large_vehicle=True):
    """is_large_vehicle: 같은 사진의 다른 차보다 확실히 큰 차인지 (모델이 없을 때 빨간색 판단에만 씀)"""
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

    # 전용 모델이 없으면 큰 빨간 차를 소방차로 봄 (빨간 승용차는 크기가 작아서 제외)
    if not is_large_vehicle:
        return False
    return _red_color_ratio(vehicle_image) >= config.FIRE_TRUCK_MIN_RED_RATIO


# 사진 속 차량마다 소방차인지 표시(vehicle["is_fire_truck"])하는 것을 담당함.
def mark_fire_trucks(image, vehicles):
    if not vehicles:
        return
    # 같은 사진 속 차량 넓이의 중앙값 (드론 높이가 달라도 사진 안에서 비교하므로 영향이 적음)
    areas = [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in (vehicle["box"] for vehicle in vehicles)]
    typical_area = float(np.median(areas))
    for vehicle, area in zip(vehicles, areas):
        # 차량 부분만 잘라서 판단함
        x1, y1, x2, y2 = vehicle["box"]
        is_large_vehicle = len(vehicles) > 1 and area >= typical_area * config.FIRE_TRUCK_MIN_SIZE_RATIO
        vehicle["is_fire_truck"] = isFireTruck(image[max(y1, 0):y2, max(x1, 0):x2], vehicle["vehicle_type"],
                                               is_large_vehicle)
