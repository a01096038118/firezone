"""Boot 전송 대기열.

사진 분석이 Boot 응답을 기다리며 멈추지 않도록, 전송은 백그라운드 스레드 한 개가
대기열에서 순서대로 처리한다. (저장 → 수정 순서가 보장됨)

- 새 단속            → sendDetection()   → POST, Boot가 준 dl_no 를 같은 날 기록에 붙임
- 같은 날 재단속(덮어쓰기) → updateDetection() → PUT (Boot 수정 API가 생기기 전에는 Flask 로그에만 남김)
"""
import json
import logging
import queue
import threading

import requests

import config
from boot.api import post_detection, put_detection
from enforcement.daily_records import get_dl_no, set_dl_no

log = logging.getLogger(__name__)

REQUEST_CREATE = "create"   # 새 탐지 기록 저장 (POST)
REQUEST_UPDATE = "update"   # 탐지 기록 수정 (PUT)

_send_queue = queue.Queue()
_sender_thread = None


# Boot에 탐지 기록을 저장하고 Boot가 준 기록번호(dl_no)를 같은 날 기록에 붙이는 것을 담당함.
def _create_detection(record_key, payload):
    dl_no = post_detection(payload)
    log.info("Boot 탐지 기록 저장 (%s, dl_no=%s)", record_key, dl_no)
    # 기록번호를 받아야 같은 날 재단속 때 수정을 보낼 수 있음
    if dl_no is None:
        log.warning("Boot 응답에서 탐지 기록번호(dl_no)를 읽지 못해 이후 수정을 보낼 수 없음 (%s)", record_key)
        return
    set_dl_no(record_key, dl_no)


# 같은 날 기록에 붙은 기록번호(dl_no)로 Boot 탐지 기록을 수정하는 것을 담당함.
def _update_detection(record_key, payload):
    # Boot에 수정 API가 없으면 보내지 않고 Flask 로그에만 남김
    if not config.BOOT_UPDATE_API_READY:
        log.info("Boot 수정 API 준비 전이라 Boot 기록 수정 생략 (%s, 마지막 탐지 %s)",
                 record_key, payload.get("dl_last_detected_at"))
        return
    # 기록번호를 모르면(첫 저장이 실패했던 경우) 새로 저장함
    dl_no = get_dl_no(record_key)
    if dl_no is None:
        log.warning("Boot 탐지 기록번호(dl_no)를 몰라 새로 저장함 (%s)", record_key)
        _create_detection(record_key, payload)
        return
    # 관리자가 기록을 지워서 수정할 기록이 없으면 새로 저장함
    if not put_detection(dl_no, payload):
        log.warning("Boot에 탐지 기록(dl_no=%s)이 없어 새로 저장함 (관리자가 삭제한 경우)", dl_no)
        _create_detection(record_key, payload)
        return
    log.info("Boot 탐지 기록 수정 (%s, dl_no=%s)", record_key, dl_no)


# 대기열에 쌓인 전송 요청을 순서대로 Boot에 보내는 것을 담당함.
def _send_loop():
    while True:
        request_type, record_key, payload = _send_queue.get()
        # Boot 없이 테스트할 때는 보낼 내용만 로그로 출력
        if not config.BOOT_ENABLED:
            log.info("[BOOT 비활성] %s %s\n%s", request_type, record_key,
                     json.dumps(payload, ensure_ascii=False, indent=2))
            continue
        # 요청 종류에 맞게 저장 또는 수정을 보냄. 실패해도 스레드는 멈추지 않음
        try:
            if request_type == REQUEST_CREATE:
                _create_detection(record_key, payload)
            else:
                _update_detection(record_key, payload)
        except requests.RequestException as error:
            log.error("Boot 전송 실패 (%s, %s): %s", request_type, record_key, error)
        except Exception:
            log.exception("Boot 전송 중 예상하지 못한 오류 (%s, %s)", request_type, record_key)


# 전송 스레드를 처음 한 번만 시작하는 것을 담당함.
def _start_sender_thread():
    global _sender_thread
    if _sender_thread is None:
        _sender_thread = threading.Thread(target=_send_loop, name="boot-sender", daemon=True)
        _sender_thread.start()


# 새 단속 기록을 Boot 저장 대기열에 넣는 것을 담당함.
def sendDetection(record_key, payload):
    """새 단속 → Boot saveDetection() 으로 새 탐지 기록 저장 요청."""
    _start_sender_thread()
    _send_queue.put((REQUEST_CREATE, record_key, payload))


# 같은 날 재단속 기록을 Boot 수정 대기열에 넣는 것을 담당함.
def updateDetection(record_key, payload):
    """같은 날 같은 차 재단속 → 기존 Boot 기록 덮어쓰기 요청."""
    _start_sender_thread()
    _send_queue.put((REQUEST_UPDATE, record_key, payload))
