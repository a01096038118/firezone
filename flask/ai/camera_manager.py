import cv2
from ai.model import recognize_plate

def detect_vehicle(image_path):
    img = cv2.imread(image_path)
    # YOLO로 차량 탐지가 가능함.
    return {"vehicle_detected": True}

def detect_illegal_parking(vehicle_info):
    # 소방차 전용구역을 판별함.
    if vehicle_info.get("vehicle_detected"):
        return "소방차 전용구역 위반"
    return "정상"

def recognize_license_plate(image_path):
    return recognize_plate(image_path)
