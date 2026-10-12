import requests
from flask import Blueprint, request, jsonify

detect_bp = Blueprint("detect", __name__)

# 차량 탐지 결과를 저장함.
@detect_bp.route("/detect", methods=["POST"])
def save_detect():
    data = request.get_json()
    car_number = data.get("car_number")
    location = data.get("location")
    time = data.get("time")

    # Boot 서버로 데이터 전달
    response = requests.post("http://localhost:8080/api/receive", json=data)

    return jsonify({"status": "sent_to_boot", "boot_response": response.text})

# 차량 탐지 결과를 조회함.
@detect_bp.route("/detect", methods=["GET"])
def list_detect():
    # DB에서 조회함.
    return jsonify([])

# 차량 탐지 결과를 삭제함.
@detect_bp.route("/detect/<car_number>", methods=["DELETE"])
def delete_detect(car_number):
    # DB에서 삭제함.
    return jsonify({"status": "deleted", "car_number": car_number})

# 차량 탐지 결과를 수정함.
@detect_bp.route("/detect/<car_number>", methods=["PUT"])
def update_detect(car_number):
    data = request.get_json()
    new_location = data.get("location")
    new_time = data.get("time")

    #DB에서 수정함.
    return jsonify({"status": "updated", "car_number": car_number})
