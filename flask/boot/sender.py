"""Boot 전송 대기열.

사진 분석이 Boot 응답을 기다리며 멈추지 않도록, 전송은 백그라운드 스레드 한 개가
대기열에서 순서대로 처리한다. (저장 → 수정 순서가 보장됨)

- 새 단속            → sendDetection()   → POST, Boot가 준 dl_no 를 같은 날 기록에 붙임
- 같은 날 재단속(덮어쓰기) → updateDetection() → PUT (Boot 수정 API가 생기기 전에는 Flask 로그에만 남김)
- 첫 저장이 실패했으면(Boot 꺼짐·거부) 같은 날 재단속 때 수정 대신 새로 저장을 다시 시도

사진을 Boot에 넘기는 방식(config.BOOT_IMAGE_UPLOAD)
- 위반할 때마다 sendDetectionWithImage() → POST(기록 + 단속 사진). 같은 날이면 Boot가 갱신
- Boot 저장에 성공한 사진은 Flask에서 지움 (사진 원본은 Boot에만)
- 그날 첫 전송이 실패하면 그 사진은 남겨두고, 다음 전송 때 먼저 보냄 (Boot가 '처음 사진'으로 보관하도록)
"""
import json
import logging
import queue
import threading

import requests

import config
from boot.api import post_detection, put_detection
from enforcement.daily_records import (clear_unsent_first, get_dl_no, get_unsent_first, is_boot_saved,
                                       mark_boot_saved, set_unsent_first)
from utils.image_storage import delete_detection_image, get_detection_image_file

log = logging.getLogger(__name__)

REQUEST_CREATE = "create"   # 새 탐지 기록 저장 (POST)
REQUEST_UPDATE = "update"   # 탐지 기록 수정 (PUT)
REQUEST_WITH_IMAGE = "with_image"   # 기록 + 단속 사진 저장·갱신 (POST multipart)

_send_queue = queue.Queue()
_sender_thread = None


# Boot에 탐지 기록을 저장하고 Boot가 준 기록번호(dl_no)를 같은 날 기록에 붙이는 것을 담당함.
def _create_detection(record_key, payload):
    # 실패하면 예외가 올라가서 저장 표시를 하지 않음 → 다음 재단속 때 다시 시도
    dl_no = post_detection(payload)
    mark_boot_saved(record_key, dl_no)
    log.info("Boot 탐지 기록 저장 (%s, dl_no=%s)", record_key, dl_no)
    # 기록번호를 받아야 같은 날 재단속 때 수정을 보낼 수 있음
    if dl_no is None:
        log.warning("Boot 응답에서 탐지 기록번호(dl_no)를 읽지 못해 이후 수정을 보낼 수 없음 (%s)", record_key)


# 기록과 단속 사진을 Boot에 보내고, 성공하면 Flask 쪽 사진을 지우는 것을 담당함.
def _post_with_image(record_key, payload, image_path):
    """실패하면 requests 예외를 그대로 올린다 (사진은 지우지 않음)."""
    dl_no = post_detection(payload, get_detection_image_file(image_path))
    mark_boot_saved(record_key, dl_no)
    delete_detection_image(image_path)
    log.info("Boot 탐지 기록·사진 저장 (%s, dl_no=%s, 마지막 탐지 %s) → Flask 사진 삭제",
             record_key, dl_no, payload.get("dl_last_detected_at"))


# 위반할 때마다 기록과 단속 사진을 Boot에 보내는 것을 담당함 (같은 날이면 Boot가 갱신).
def _send_with_image(record_key, payload, image_path):
    # 1. 그날 첫 단속을 아직 못 보냈으면 그것부터 보냄 (Boot가 처음 사진으로 보관)
    unsent_first = get_unsent_first(record_key)
    if unsent_first and unsent_first["image_path"] != image_path:
        _post_with_image(record_key, unsent_first["payload"], unsent_first["image_path"])
        clear_unsent_first(record_key)

    # 2. 이번 단속을 보냄
    try:
        _post_with_image(record_key, payload, image_path)
    except Exception:
        # 그날 아직 아무것도 못 보냈으면 이 사진이 첫 사진 → 남겨두고 다음 전송 때 먼저 보냄
        if not is_boot_saved(record_key) and get_unsent_first(record_key) is None:
            set_unsent_first(record_key, payload, image_path)
            log.info("Boot 첫 전송 실패 → 첫 단속 사진을 남겨두고 다음 전송 때 다시 보냄 (%s)", record_key)
        else:
            # 중간 사진은 Boot도 남기지 않으므로 지움 (다음 단속 때 더 최신 사진이 감)
            delete_detection_image(image_path)
        raise


# 같은 날 기록에 붙은 기록번호(dl_no)로 Boot 탐지 기록을 수정하는 것을 담당함.
def _update_detection(record_key, payload):
    # 첫 저장이 실패했던 기록이면 수정 대신 새로 저장을 다시 시도
    if not is_boot_saved(record_key):
        log.info("Boot에 아직 저장되지 않은 기록이라 새로 저장을 다시 시도함 (%s)", record_key)
        _create_detection(record_key, payload)
        return
    # Boot에 수정 API가 없으면 보내지 않고 Flask 로그에만 남김
    if not config.BOOT_UPDATE_API_READY:
        log.info("Boot 수정 API 준비 전이라 Boot 기록 수정 생략 (%s, 마지막 탐지 %s)",
                 record_key, payload.get("dl_last_detected_at"))
        return
    # 저장은 됐지만 기록번호를 못 받았으면 수정할 수 없음 (새로 저장하면 같은 기록이 두 번 생김)
    dl_no = get_dl_no(record_key)
    if dl_no is None:
        log.warning("Boot 탐지 기록번호(dl_no)를 몰라 Boot 기록 수정 생략 (%s)", record_key)
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
        request_type, record_key, payload, image_path = _send_queue.get()
        # Boot 없이 테스트할 때는 보낼 내용만 로그로 출력 (사진은 지우지 않음)
        if not config.BOOT_ENABLED:
            log.info("[BOOT 비활성] %s %s 사진=%s\n%s", request_type, record_key, image_path,
                     json.dumps(payload, ensure_ascii=False, indent=2))
            continue
        # 요청 종류에 맞게 저장 또는 수정을 보냄. 실패해도 스레드는 멈추지 않음
        try:
            if request_type == REQUEST_WITH_IMAGE:
                _send_with_image(record_key, payload, image_path)
            elif request_type == REQUEST_CREATE:
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
    _send_queue.put((REQUEST_CREATE, record_key, payload, None))


# 같은 날 재단속 기록을 Boot 수정 대기열에 넣는 것을 담당함.
def updateDetection(record_key, payload):
    """같은 날 같은 차 재단속 → 기존 Boot 기록 덮어쓰기 요청."""
    _start_sender_thread()
    _send_queue.put((REQUEST_UPDATE, record_key, payload, None))


# 단속(새 단속·같은 날 재단속 모두)을 사진과 함께 Boot 대기열에 넣는 것을 담당함.
def sendDetectionWithImage(record_key, payload, image_path):
    """사진을 Boot에 넘기는 방식(config.BOOT_IMAGE_UPLOAD). image_path: data/detections 기준 상대 경로"""
    _start_sender_thread()
    _send_queue.put((REQUEST_WITH_IMAGE, record_key, payload, image_path))
