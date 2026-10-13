import requests
import cv2
from flask import Blueprint, request, jsonify, Response
from ai.camera_manager import detect_vehicle, detect_illegal_parking, recognize_license_plate

detect_bp = Blueprint("detect", __name__)

@detect_bp.route("/upload", methods=["POST"])
def detectVehicle():
    file = request.files["image"]
    save_path = f"./uploads/{file.filename}"
    file.save(save_path)

    vehicle_info = detect_vehicle(save_path)
    violation_info = detect_illegal_parking(vehicle_info)
    plate_number = recognize_license_plate(save_path)

    payload = {
        "dl_camera_id": "DRONE01",
        "dl_zone_no": "소방차전용구역",
        "dl_violation_type": violation_info,
        "dl_car_number": plate_number,
        "dl_image_path": save_path
    }

    # Boot 서버로 전달함.
    response = requests.post("http://localhost:8080/api/detection", json=payload)

    return jsonify({"status": "sent_to_boot", "boot_response": response.text, "payload": payload})

def generate_frames():
    cap = cv2.VideoCapture(0)  # 0 = 기본 웹캠, 필요 시 RTSP/드론 URL로 교체 가능
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # JPEG 인코딩
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@detect_bp.route("/monitor", methods=["GET"])
def monitorLive():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')