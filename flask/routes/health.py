"""상태 확인 API."""
from flask import Blueprint, jsonify

from boot.api import check_boot_connection
from camera.camera_config import load_zones
from camera.monitoring import get_all_camera_status

health_bp = Blueprint("health", __name__)


# 서버·Boot·카메라 상태 확인 API(GET /api/health)를 담당함.
@health_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "flask": "ok",
        "boot": check_boot_connection(),
        "zones": [zone["zone_no"] for zone in load_zones()],
        "cameras": [{key: status[key] for key in ("camera_id", "connected", "fps", "detection_failed")}
                    for status in get_all_camera_status()],
    })
