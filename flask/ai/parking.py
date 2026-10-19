"""불법주정차 판정 (MON-003): 1차·2차 촬영 비교.

단속 조건 (세 가지 모두)
  1) 1차·2차 사진의 차량번호가 완전히 같음 (한글까지)
  2) 같은 자리 (기준 사진 좌표에서 두 박스가 SAME_SPOT_MIN_OVERLAP 이상 겹침)
  3) 1차 촬영부터 VIOLATION_STAY_SECONDS 이상 지남 (같은 날)

구역마다 "차량번호 → 그 차를 처음 본 촬영(1차)" 을 기억한다 (sightings).
- 처음 보는 번호 / 자리가 바뀐 차 → 이번 촬영이 1차가 됨
- 시간이 아직 모자라면 1차를 그대로 두고 다음 촬영에서 다시 비교
- 이번 촬영에서 안 보이는 번호 → 떠난 것으로 보고 지움
"""
from dataclasses import dataclass
from typing import Optional

import config
from ai.shot import ParkedCar, Shot
from ai.zone import box_overlap_ratio
from utils.time_format import is_same_day

# 차량별 판정 결과
STATUS_VIOLATION = "위반 확정"
STATUS_FIRST_SHOT = "1차 촬영 (다음 촬영과 비교)"
STATUS_MOVED = "자리 이동 (이번 촬영을 1차로 다시 비교)"
STATUS_NOT_ENOUGH_TIME = "정차 시간 부족 (다음 촬영과 다시 비교)"
STATUS_PLATE_UNREADABLE = "판정 불가 (번호판 식별불가)"


# 어떤 차를 처음 본 촬영(1차)의 보관을 담당함.
@dataclass
class Sighting:
    shot: Shot
    car: ParkedCar


# 차량 한 대의 판정 결과 보관을 담당함.
@dataclass
class CarJudgment:
    status: str
    car: ParkedCar                          # 이번(2차) 촬영의 차량
    first_sighting: Optional[Sighting] = None   # 같은 번호 차량을 처음 본 1차 촬영
    stay_seconds: float = 0                 # 1차~이번 촬영 시간 차이


# 1차 촬영과 이번 촬영을 비교해서 차량마다 위반 여부를 판정하는 것을 담당함.
def detectIllegalParking(sightings, second_shot: Shot):
    """sightings: {차량번호: Sighting} (같은 구역에서 이전에 본 차량들)
    second_shot: 이번 촬영. 구역 안 차량마다 CarJudgment 를 돌려준다."""
    judgments = []
    for car in second_shot.cars:
        # 번호판을 못 읽으면 같은 차인지 확인할 수 없음
        if not car.car_number:
            judgments.append(CarJudgment(STATUS_PLATE_UNREADABLE, car))
            continue

        # 같은 날 같은 번호를 본 적이 없으면 이번이 1차
        sighting = sightings.get(car.car_number)
        if sighting is None or not is_same_day(sighting.shot.captured_at, second_shot.captured_at):
            judgments.append(CarJudgment(STATUS_FIRST_SHOT, car))
            continue

        stay_seconds = second_shot.captured_at - sighting.shot.captured_at
        # 같은 번호지만 자리가 바뀌었으면 단속하지 않고 이번을 1차로 다시 봄
        if box_overlap_ratio(sighting.car.reference_box, car.reference_box) < config.SAME_SPOT_MIN_OVERLAP:
            judgments.append(CarJudgment(STATUS_MOVED, car, sighting, stay_seconds))
            continue
        # 같은 차, 같은 자리지만 시간이 모자라면 아직 단속하지 않음
        if stay_seconds < config.VIOLATION_STAY_SECONDS:
            judgments.append(CarJudgment(STATUS_NOT_ENOUGH_TIME, car, sighting, stay_seconds))
            continue
        # 세 조건을 모두 만족 → 위반 확정
        judgments.append(CarJudgment(STATUS_VIOLATION, car, sighting, stay_seconds))
    return judgments


# 판정 결과에 맞게 "처음 본 촬영" 기록을 고치는 것을 담당함.
def update_sightings(sightings, second_shot: Shot, judgments):
    """판정 뒤에 호출한다. 새 sightings dict 를 돌려준다."""
    updated_sightings = {}
    unreadable_cars = [judgment.car for judgment in judgments if judgment.status == STATUS_PLATE_UNREADABLE]

    for judgment in judgments:
        car_number = judgment.car.car_number
        if not car_number:
            continue
        # 처음 봤거나 자리를 옮긴 차는 이번 촬영이 새 1차
        if judgment.status in (STATUS_FIRST_SHOT, STATUS_MOVED):
            updated_sightings[car_number] = Sighting(second_shot, judgment.car)
        # 시간 부족·위반 확정은 처음 본 1차를 그대로 유지 (머문 시간을 계속 이어서 계산)
        else:
            updated_sightings[car_number] = judgment.first_sighting

    # 이번에 번호판을 못 읽은 차와 같은 자리에 있던 차는 떠난 게 아닐 수 있으니 유지
    for car_number, sighting in sightings.items():
        if car_number in updated_sightings:
            continue
        if any(box_overlap_ratio(sighting.car.reference_box, car.reference_box) >= config.SAME_SPOT_MIN_OVERLAP
               for car in unreadable_cars):
            updated_sightings[car_number] = sighting
    # 나머지(이번 촬영에서 안 보인 번호)는 떠난 것으로 보고 지움
    return updated_sightings
