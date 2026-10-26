"""촬영 사진 한 장 분석: 차량 탐지 → 구역 찾기 → 소방차 제외 → 구역 안 차량 → 번호판.

구역은 ① 등록된 구역 사진과 맞춰 찾고, ② 맞는 구역이 없으면 바닥 표시(노란 테두리)로 직접 찾는다.

결과는 ai/shot.py 의 Shot (1차·2차 비교에 쓰는 촬영 결과).
분석할 수 없으면 UndecidablePhoto 예외로 이유를 알려준다 (판정 불가).
"""
import logging

import config
from ai.fire_truck import mark_fire_trucks
from ai.plate_reader import read_plate_and_wait
from ai.shot import ParkedCar, Shot
from ai.vehicle import detectVehicle
from ai.zone import box_to_reference, get_ground_point, ground_box_to_reference, is_point_in_photo_polygon, zone_polygon_in_photo
from ai.zone_finder import MATCH_METHOD_AUTO_MARKING, find_zone_by_marking
from ai.zone_matcher import find_zone_in_photo
from camera.camera_config import load_zones
from utils.image_storage import save_photo

log = logging.getLogger(__name__)

REASON_NO_ZONE = "구역 확인 불가"
REASON_DETECTION_FAILED = "차량 탐지 실패"


# 사진을 분석할 수 없는 경우(판정 불가)와 그 이유 전달을 담당함.
class UndecidablePhoto(Exception):
    # 판정 불가 이유와 구역번호를 담는 것을 담당함.
    def __init__(self, reason, zone_no=None, detail=""):
        super().__init__(reason)
        self.reason = reason
        self.zone_no = zone_no
        self.detail = detail


# 등록된 구역 사진 또는 바닥 표시로 사진 속 구역을 찾는 것을 담당함.
def _find_zone(photo, vehicles, default_zone_no):
    # 1. 등록된 구역 사진과 맞춰봄 (가장 정확함)
    zone_match = find_zone_in_photo(photo, load_zones(), default_zone_no)
    if zone_match is not None:
        return zone_match
    # 2. 등록된 곳이 아니면 바닥 표시로 직접 찾음 (차량 위 색은 바닥 칠로 보지 않게 차량 박스를 넘김)
    if config.AUTO_ZONE_ENABLED:
        return find_zone_by_marking(photo, [vehicle["box"] for vehicle in vehicles])
    return None


# 촬영 사진 한 장을 분석해서 Shot 을 만드는 것을 담당함.
def analyze_photo(camera_id, photo, captured_at, default_zone_no=None):
    """반환: Shot. 구역을 못 찾거나 차량 탐지에 실패하면 UndecidablePhoto 예외."""
    # 1. 차량 탐지 (모델 오류는 판정 불가로 처리)
    try:
        vehicles = detectVehicle(photo)
    except Exception as error:
        log.exception("[%s] 차량 탐지 실패", camera_id)
        raise UndecidablePhoto(REASON_DETECTION_FAILED, detail=str(error))

    # 2. 어느 구역인지 찾음 (등록된 구역 사진 → 바닥 표시 순서)
    zone_match = _find_zone(photo, vehicles, default_zone_no)
    if zone_match is None:
        raise UndecidablePhoto(REASON_NO_ZONE, detail="등록된 구역 사진과 맞지 않고 바닥 표시도 찾지 못함")
    zone, photo_to_reference = zone_match["zone"], zone_match["photo_to_reference"]
    polygon_in_photo = zone_polygon_in_photo(zone, photo_to_reference)
    # 바닥 표시로 찾은 구역은 차량 지붕이 크게 늘어나므로 바닥 부분만으로 같은 자리를 비교
    to_reference_box = ground_box_to_reference if zone_match["method"] == MATCH_METHOD_AUTO_MARKING else box_to_reference

    # 3. 소방차 표시 → 소방차가 아닌 차량 중 구역 안에 있는 차량만 남김
    mark_fire_trucks(photo, vehicles)
    cars_in_zone = []
    for vehicle in vehicles:
        # 바퀴가 닿는 지점이 사진 위 구역 테두리 안인지 봄
        if vehicle["is_fire_truck"] or not is_point_in_photo_polygon(get_ground_point(vehicle["box"]), polygon_in_photo):
            continue
        # 4. 구역 안 차량만 번호판을 읽음 (차 안에서만 읽음)
        x1, y1, x2, y2 = vehicle["box"]
        car_number = read_plate_and_wait(photo[max(y1, 0):y2, max(x1, 0):x2])
        cars_in_zone.append(ParkedCar(
            vehicle_type=vehicle["vehicle_type"],
            box=vehicle["box"],
            reference_box=to_reference_box(vehicle["box"], photo_to_reference),
            car_number=car_number,
        ))

    # 5. 원본 사진 저장 후 촬영 결과로 묶음
    fire_truck_count = sum(1 for vehicle in vehicles if vehicle["is_fire_truck"])
    log.info("[%s] 구역 %s (%s) 차량 %d대, 소방차 %d대, 구역 안 일반 차량 %d대 %s",
             camera_id, zone["zone_no"], zone_match["method"], len(vehicles), fire_truck_count,
             len(cars_in_zone), [car.car_number or "번호판 미인식" for car in cars_in_zone])
    # 사진을 Boot에 넘기는 방식이면 원본은 파일로 남기지 않음 (1차·2차 비교는 메모리의 사진으로 함)
    photo_path = None if config.BOOT_IMAGE_UPLOAD else save_photo(camera_id, zone["zone_no"], photo, captured_at)
    return Shot(
        camera_id=camera_id,
        zone_no=zone["zone_no"],
        zone_name=zone["name"],
        violation_type=zone["violation_type"],
        captured_at=captured_at,
        image=photo,
        photo_path=photo_path,
        match_method=zone_match["method"],
        zone_polygon_in_photo=polygon_in_photo,
        cars=cars_in_zone,
    )
