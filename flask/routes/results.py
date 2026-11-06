"""처리 결과·구역 목록 API."""
from flask import Blueprint, jsonify

from camera.camera_config import load_zones
from enforcement.enforcement_service import get_recent_results

results_bp = Blueprint("results", __name__)


# 최근 단속 처리 결과 API(GET /api/results)를 담당함.
@results_bp.route("/results", methods=["GET"])
def list_recent_results():
    """최근 촬영 처리 결과 (최신순, 최대 30건). 실제 탐지 기록은 Boot DB 에 있다."""
    return jsonify(get_recent_results())


# 등록된 구역 목록 API(GET /api/zones)를 담당함.
@results_bp.route("/zones", methods=["GET"])
def list_zones():
    # 화면에 필요한 정보만 보여줌
    return jsonify([{"zone_no": zone["zone_no"], "name": zone["name"],
                     "violation_type": zone["violation_type"], "reference_image": zone["reference_image"]}
                    for zone in load_zones()])
