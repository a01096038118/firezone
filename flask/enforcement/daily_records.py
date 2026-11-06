"""같은 날 덮어쓰기용 단속 기록.

같은 날, 같은 카메라, 같은 구역, 같은 차량번호면 기록 1건만 둔다.
처음 단속되면 새 기록을 만들고, 그날 다시 단속되면 그 기록을 덮어쓴다.
서버를 다시 켜도 이어지도록 data/daily_records.json 에 저장한다 (오늘 것만 보관).
"""
import json
import logging
import os
import threading
from datetime import date, datetime

import config
from utils.image_storage import delete_detection_image

log = logging.getLogger(__name__)

_records_lock = threading.Lock()
_records_by_key = None   # 처음 쓸 때 파일에서 읽음


# 기록을 구분하는 key 를 만드는 것을 담당함.
def make_record_key(camera_id, zone_no, car_number, timestamp):
    """예: 2026-10-19|DRONE01|Z01|12가3456"""
    return f"{datetime.fromtimestamp(timestamp):%Y-%m-%d}|{camera_id}|{zone_no}|{car_number}"


# 기록 번호(위반 로그에 쓰는 번호)를 만드는 것을 담당함.
def make_record_number(camera_id, zone_no, car_number, timestamp):
    """예: DRONE01-Z01-20261019-12가3456 (같은 날 같은 차는 항상 같은 번호)"""
    return f"{camera_id}-{zone_no}-{datetime.fromtimestamp(timestamp):%Y%m%d}-{car_number}"


# 파일에서 오늘 기록만 읽어오는 것을 담당함.
def _load_today_records():
    if not os.path.exists(config.DAILY_RECORD_FILE):
        return {}
    try:
        with open(config.DAILY_RECORD_FILE, encoding="utf-8") as record_file:
            saved_records = json.load(record_file)
    except (OSError, ValueError):
        log.exception("같은 날 기록 파일을 읽지 못해 빈 기록으로 시작함")
        return {}
    # 지난 날짜 기록은 버림 (덮어쓰기는 같은 날만)
    today_prefix = f"{date.today():%Y-%m-%d}|"
    for key, record in saved_records.items():
        # 지난 날짜에 Boot로 끝내 못 보낸 첫 단속 사진은 더 보낼 일이 없으므로 지움
        unsent_first = record.get("unsent_first")
        if not key.startswith(today_prefix) and unsent_first:
            delete_detection_image(unsent_first.get("image_path"))
    return {key: record for key, record in saved_records.items() if key.startswith(today_prefix)}


# 기록을 파일에 저장하는 것을 담당함.
def _save_records():
    os.makedirs(os.path.dirname(config.DAILY_RECORD_FILE), exist_ok=True)
    # 임시 파일에 쓴 뒤 바꿔치기 (쓰는 도중 꺼져도 파일이 깨지지 않게)
    temp_path = config.DAILY_RECORD_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as record_file:
        json.dump(_records_by_key, record_file, ensure_ascii=False, indent=2)
    os.replace(temp_path, config.DAILY_RECORD_FILE)


# 기록 목록을 처음 한 번만 읽어오는 것을 담당함.
def _get_records():
    global _records_by_key
    if _records_by_key is None:
        _records_by_key = _load_today_records()
    return _records_by_key


# 같은 날 같은 차의 기록을 찾는 것을 담당함.
def find_record(record_key):
    """있으면 {"record_number", "first_detected_at", "last_detected_at", "image_path", "dl_no", "boot_saved",
    "unsent_first"}, 없으면 None."""
    with _records_lock:
        record = _get_records().get(record_key)
        return dict(record) if record else None


# 새 기록을 만들거나 기존 기록을 덮어쓰는 것을 담당함.
def save_record(record_key, record):
    with _records_lock:
        # Boot 응답·전송 상태로 정해지는 값(dl_no, boot_saved, unsent_first)은 유지
        existing_record = _get_records().get(record_key, {})
        _get_records()[record_key] = {
            **record,
            "dl_no": record.get("dl_no", existing_record.get("dl_no")),
            "boot_saved": existing_record.get("boot_saved", False),
            "unsent_first": existing_record.get("unsent_first"),
        }
        _save_records()


# Boot에 못 보낸 그날 첫 단속(내용과 사진)을 기억하는 것을 담당함.
def set_unsent_first(record_key, payload, image_path):
    """Boot는 처음 받은 사진을 '처음 사진'으로 보관하므로, 첫 전송이 실패하면 다음 전송 때 이것부터 다시 보낸다."""
    with _records_lock:
        record = _get_records().get(record_key)
        if record is not None:
            record["unsent_first"] = {"payload": payload, "image_path": image_path}
            _save_records()


# Boot에 못 보낸 그날 첫 단속을 꺼내는 것을 담당함.
def get_unsent_first(record_key):
    """반환: {"payload", "image_path"} 또는 None"""
    with _records_lock:
        unsent_first = _get_records().get(record_key, {}).get("unsent_first")
        return dict(unsent_first) if unsent_first else None


# Boot에 못 보낸 첫 단속 기억을 지우는 것을 담당함.
def clear_unsent_first(record_key):
    with _records_lock:
        record = _get_records().get(record_key)
        if record is not None and record.get("unsent_first"):
            record["unsent_first"] = None
            _save_records()


# Boot 저장에 성공했다고 표시하고, Boot가 돌려준 탐지 기록번호(dl_no)를 붙이는 것을 담당함.
def mark_boot_saved(record_key, dl_no):
    """dl_no 를 못 받았어도(None) 저장은 된 것이므로 다시 저장하지 않게 표시한다."""
    with _records_lock:
        record = _get_records().get(record_key)
        if record is not None:
            record["boot_saved"] = True
            record["dl_no"] = dl_no
            _save_records()


# 이 기록이 Boot에 저장됐는지 확인하는 것을 담당함.
def is_boot_saved(record_key):
    """첫 저장이 실패했으면 False → 같은 날 다시 단속될 때 새로 저장을 다시 시도한다."""
    with _records_lock:
        return bool(_get_records().get(record_key, {}).get("boot_saved"))


# 기록에 붙은 Boot 탐지 기록번호(dl_no)를 꺼내는 것을 담당함.
def get_dl_no(record_key):
    with _records_lock:
        return _get_records().get(record_key, {}).get("dl_no")
