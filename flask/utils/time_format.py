"""시간 형식 변환."""
from datetime import datetime

import config

KOREAN_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"      # 사진 EXIF 촬영 시각 형식
INPUT_DATETIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M")  # 직접 입력 형식


# 시간을 Boot 전송 형식(yyyy-MM-ddTHH:mm:ss)으로 바꾸는 것을 담당함.
def format_boot_datetime(timestamp):
    """timestamp → "2026-10-19T10:00:15" (Boot LocalDateTime 형식)"""
    return datetime.fromtimestamp(timestamp).strftime(config.BOOT_DATETIME_FORMAT)


# 시간을 사람이 읽는 형식으로 바꾸는 것을 담당함.
def format_readable_datetime(timestamp):
    """timestamp → "2026-10-19 10:00:15" """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# 날짜를 "2026년 10월 19일 (월)" 처럼 바꾸는 것을 담당함.
def format_korean_date(timestamp):
    taken_at = datetime.fromtimestamp(timestamp)
    return f"{taken_at:%Y년 %m월 %d일} ({KOREAN_WEEKDAYS[taken_at.weekday()]})"


# 두 시각이 같은 날인지 확인하는 것을 담당함.
def is_same_day(first_timestamp, second_timestamp):
    return datetime.fromtimestamp(first_timestamp).date() == datetime.fromtimestamp(second_timestamp).date()


# 머문 시간(초)을 "2분 10초" 처럼 바꾸는 것을 담당함.
def format_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    # 시간이 있으면 시·분, 분이 있으면 분·초, 아니면 초만
    if hours:
        return f"{hours}시간 {minutes}분"
    return f"{minutes}분 {seconds}초" if minutes else f"{seconds}초"


# 직접 입력한 촬영 시각 글자를 timestamp 로 바꾸는 것을 담당함.
def parse_input_datetime(text):
    """"2026-10-19 10:00:00" 같은 입력 → timestamp. 형식이 틀리면 None."""
    if not text:
        return None
    # 허용하는 형식을 차례로 시도함
    for time_format in INPUT_DATETIME_FORMATS:
        try:
            return datetime.strptime(text.strip(), time_format).timestamp()
        except ValueError:
            continue
    return None


# 사진 EXIF 촬영 시각 글자를 timestamp 로 바꾸는 것을 담당함.
def parse_exif_datetime(text):
    """"2026:10:19 10:00:00" → timestamp. 형식이 틀리면 None."""
    try:
        return datetime.strptime(str(text).strip().rstrip("\x00"), EXIF_DATETIME_FORMAT).timestamp()
    except ValueError:
        return None
