"""촬영 한 번의 결과(구역, 시각, 구역 안 차량)를 담는 자료 구조."""
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# 구역 안에 서 있는 차량 한 대의 정보 보관을 담당함.
@dataclass
class ParkedCar:
    vehicle_type: str
    box: tuple                    # 사진 속 차량 박스 (픽셀)
    reference_box: tuple          # 기준 사진 좌표로 바꾼 차량 박스 (같은 자리 비교용)
    car_number: Optional[str]     # 읽은 차량번호, 못 읽으면 None


# 촬영 한 번(사진 한 장)의 분석 결과 보관을 담당함.
@dataclass
class Shot:
    camera_id: str
    zone_no: str
    zone_name: str
    violation_type: str
    captured_at: float            # 촬영 시각 (timestamp)
    image: np.ndarray             # 촬영 원본 사진
    photo_path: Optional[str]     # 저장된 원본 사진 경로 (data/photos 기준). 사진을 Boot에 넘기는 방식이면 None
    match_method: str             # 구역을 맞춘 방법 (자동 맞추기 / 고정 좌표)
    zone_polygon_in_photo: list   # 사진 위 구역 테두리 (화면에 그릴 때 사용)
    cars: List[ParkedCar] = field(default_factory=list)   # 구역 안 일반 차량 (소방차 제외)
