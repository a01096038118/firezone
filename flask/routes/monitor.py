"""실시간 관제 API (MON-001)."""
import time

from flask import Blueprint, Response, jsonify

from camera.monitoring import get_all_camera_status, get_camera_monitor

monitor_bp = Blueprint("monitor", __name__)

STREAM_MAX_FPS = 15


# 최신 관제 화면(JPEG)을 계속 내보내는 것을 담당함.
def _generate_mjpeg(camera_monitor):
    last_sent_jpeg = None
    while True:
        jpeg_bytes = camera_monitor.latest_jpeg
        # 새 화면이 있을 때만 보냄 (같은 화면을 반복해서 보내지 않음)
        if jpeg_bytes is not None and jpeg_bytes is not last_sent_jpeg:
            last_sent_jpeg = jpeg_bytes
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
        time.sleep(1 / STREAM_MAX_FPS)


# 실시간 관제 영상 API(GET /api/monitor/<camera_id>)를 담당함.
@monitor_bp.route("/monitor/<camera_id>", methods=["GET"])
def stream_camera(camera_id):
    """<img src="http://Flask주소:5000/api/monitor/DRONE01"> 로 바로 쓰는 MJPEG 영상."""
    camera_monitor = get_camera_monitor(camera_id)
    if camera_monitor is None:
        return jsonify({"error": f"카메라 {camera_id} 가 없거나 꺼져 있습니다."}), 404
    return Response(_generate_mjpeg(camera_monitor), mimetype="multipart/x-mixed-replace; boundary=frame")


# 카메라 목록과 연결·자동 촬영 상태 API(GET /api/cameras)를 담당함.
@monitor_bp.route("/cameras", methods=["GET"])
def list_cameras():
    return jsonify(get_all_camera_status())
