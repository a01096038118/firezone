"""단속 처리 전체 흐름 (자동 촬영과 사진 올리기가 함께 사용).

사진 분석 → 구역의 1차 촬영 기록과 비교(detectIllegalParking) → 위반 처리 → 1차 기록 갱신
"""
import logging
import threading
from collections import deque

from ai.parking import STATUS_PLATE_UNREADABLE, STATUS_VIOLATION, detectIllegalParking, update_sightings
from enforcement.photo_analyzer import UndecidablePhoto, analyze_photo
from enforcement.sighting_store import get_sightings, set_sightings
from enforcement.violation_handler import handle_violation
from utils.image_storage import get_photo_url
from utils.time_format import format_duration, format_readable_datetime
from utils.violation_log import write_undecidable

log = logging.getLogger(__name__)

RECENT_RESULT_COUNT = 30
# 같은 구역 사진 두 장이 동시에 처리되면 1차 기록이 꼬이므로 한 장씩 처리
_processing_lock = threading.Lock()
# 화면(테스트 페이지)에 보여줄 최근 처리 결과
_recent_results = deque(maxlen=RECENT_RESULT_COUNT)
_recent_results_lock = threading.Lock()


# 처리 결과를 최근 결과 목록에 넣는 것을 담당함.
def _remember_result(result):
    with _recent_results_lock:
        _recent_results.appendleft(result)


# 최근 처리 결과 목록을 꺼내는 것을 담당함.
def get_recent_results():
    with _recent_results_lock:
        return list(_recent_results)


# 판정 결과 한 건을 화면에 보여줄 dict 로 바꾸는 것을 담당함.
def _judgment_to_dict(judgment):
    return {
        "car_number": judgment.car.car_number,
        "vehicle_type": judgment.car.vehicle_type,
        "status": judgment.status,
        "stay": format_duration(judgment.stay_seconds) if judgment.first_sighting else None,
    }


# 촬영 사진 한 장으로 단속 처리 전체를 하는 것을 담당함.
def process_photo(camera_id, photo, captured_at, source, default_zone_no=None):
    """source: "자동 촬영" / "사진 올리기". 반환: 처리 결과 dict (화면·API 응답용)"""
    result = {"camera_id": camera_id, "source": source,
              "captured_at": format_readable_datetime(captured_at), "violations": []}
    with _processing_lock:
        # 1. 사진 분석 (구역을 못 찾거나 탐지에 실패하면 판정 불가)
        try:
            shot = analyze_photo(camera_id, photo, captured_at, default_zone_no)
        except UndecidablePhoto as undecidable:
            write_undecidable(undecidable.reason, camera_id, captured_at, undecidable.zone_no, undecidable.detail)
            result.update(status=f"판정 불가 ({undecidable.reason})", zone_no=undecidable.zone_no)
            _remember_result(result)
            return result

        # 2. 같은 구역에서 이전에 본 차량(1차)과 비교
        sightings = get_sightings(camera_id, shot.zone_no)
        judgments = detectIllegalParking(sightings, shot)
        set_sightings(camera_id, shot.zone_no, update_sightings(sightings, shot, judgments))

    # 3. 번호판을 못 읽은 차량은 판정 불가로 기록
    unreadable_count = sum(1 for judgment in judgments if judgment.status == STATUS_PLATE_UNREADABLE)
    if unreadable_count:
        write_undecidable("번호판 식별불가", camera_id, captured_at, shot.zone_no, f"차량 {unreadable_count}대")

    # 4. 위반 확정 차량을 기록하고 Boot에 보냄
    for judgment in judgments:
        if judgment.status == STATUS_VIOLATION:
            result["violations"].append(handle_violation(shot, judgment))

    # 5. 결과 정리
    result.update(
        status=f"위반 {len(result['violations'])}건" if result["violations"] else "위반 없음",
        zone_no=shot.zone_no, zone_name=shot.zone_name, match_method=shot.match_method,
        photo_url=get_photo_url(shot.photo_path),
        zone_polygon=[list(point) for point in shot.zone_polygon_in_photo],   # 실시간 화면에 구역을 그릴 때 사용
        cars=[_judgment_to_dict(judgment) for judgment in judgments],
    )
    log.info("[%s] %s 촬영 처리 완료 (%s, 구역 %s): %s",
             camera_id, source, result["captured_at"], shot.zone_no, result["status"])
    _remember_result(result)
    return result
