"""구역마다 "차량번호 → 그 차를 처음 본 촬영(1차)" 보관 (ai/parking.py 참고).

서버 메모리에만 둔다. 서버를 다시 켜면 1차 촬영부터 다시 시작한다.
"""
import threading

_sightings_lock = threading.Lock()
# (카메라 ID, 구역번호) → {차량번호: Sighting}
_sightings_by_zone = {}


# 구역의 "처음 본 촬영" 목록을 꺼내는 것을 담당함.
def get_sightings(camera_id, zone_no):
    with _sightings_lock:
        # 바깥에서 고쳐도 원본이 바뀌지 않게 복사해서 돌려줌
        return dict(_sightings_by_zone.get((camera_id, zone_no), {}))


# 구역의 "처음 본 촬영" 목록을 새것으로 바꾸는 것을 담당함.
def set_sightings(camera_id, zone_no, sightings):
    with _sightings_lock:
        _sightings_by_zone[(camera_id, zone_no)] = dict(sightings)


# 모든 구역의 기록을 지우는 것을 담당함 (테스트용).
def clear_all_sightings():
    with _sightings_lock:
        _sightings_by_zone.clear()
