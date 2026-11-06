"""위반 기록 로그 (과태료 고지서 형식) + 판정 불가 기록.

logs/violation_2026-10-19.log 예시
    ─────────── 불법주정차 위반 기록 ───────────
    기록번호 : DRONE01-Z01-20261019-12가3456
    처리     : 새 기록
    위반일시 : 2026년 10월 19일 (일)
    위반시각 : 10:00:00 (1차 촬영) ~ 10:00:15 (2차 촬영)  15초 정차 확인
    차량번호 : 12가3456
    위반장소 : DRONE01 / 구역 Z01 (소방차 전용구역)
    단속사진 : data/detections/2026-10-19/100015_DRONE01_Z01.jpg
    ────────────────────────────────────────────
    [판정 불가] 10:05:00 DRONE01 / 구역 Z01 : 번호판 식별불가 (차량 1대)
"""
import logging
from datetime import datetime

from utils.logger import VIOLATION_LOGGER_NAME
from utils.time_format import format_duration, format_korean_date

violation_logger = logging.getLogger(VIOLATION_LOGGER_NAME)

ACTION_NEW_RECORD = "새 기록"
ACTION_OVERWRITE = "같은 날 재단속 → 기존 기록 덮어쓰기"


# 단속이 확정됐을 때 고지서 형식의 위반 기록을 남기는 것을 담당함.
def write_violation_record(record_number, action, camera_id, zone_no, zone_name,
                           car_number, first_detected_at, last_detected_at, evidence_image_path):
    first_time, last_time = datetime.fromtimestamp(first_detected_at), datetime.fromtimestamp(last_detected_at)
    # 1차~2차 시각과 머문 시간
    violation_time = (f"{first_time:%H:%M:%S} (1차 촬영) ~ {last_time:%H:%M:%S} (2차 촬영)  "
                      f"{format_duration(last_detected_at - first_detected_at)} 정차 확인")
    violation_logger.info("\n".join([
        "─────────── 불법주정차 위반 기록 ───────────",
        f"기록번호 : {record_number}",
        f"처리     : {action}",
        f"위반일시 : {format_korean_date(first_detected_at)}",
        f"위반시각 : {violation_time}",
        f"차량번호 : {car_number}",
        f"위반장소 : {camera_id} / 구역 {zone_no} ({zone_name})",
        f"단속사진 : data/detections/{evidence_image_path}",
        "────────────────────────────────────────────",
    ]))


# 단속할 수 없었던 경우(판정 불가)를 한 줄로 남기는 것을 담당함.
def write_undecidable(reason, camera_id, captured_at, zone_no=None, detail=""):
    """reason 예: "번호판 식별불가", "구역 확인 불가", "사진 흐림", "촬영 시각 없음", "차량 탐지 실패" """
    place = f"{camera_id} / 구역 {zone_no}" if zone_no else camera_id
    detail_text = f" ({detail})" if detail else ""
    violation_logger.info("[판정 불가] %s %s : %s%s",
                          f"{datetime.fromtimestamp(captured_at):%H:%M:%S}", place, reason, detail_text)
