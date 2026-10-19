"""자동 촬영 사진 처리 대기열.

사진 분석(구역 맞추기·차량 탐지·번호판 OCR)은 몇 초 걸려서, 실시간 화면이 멈추지 않도록
촬영한 사진은 대기열에 넣고 백그라운드 스레드 한 개가 순서대로 처리한다.
"""
import logging
import queue
import threading

from enforcement.enforcement_service import process_photo

log = logging.getLogger(__name__)

SOURCE_AUTO_CAPTURE = "자동 촬영"

_capture_queue = queue.Queue()
_worker_thread = None


# 대기열의 촬영 사진을 순서대로 단속 처리하는 것을 담당함.
def _process_loop():
    while True:
        camera_id, photo, captured_at, default_zone_no, on_done = _capture_queue.get()
        # 처리 중 오류가 나도 스레드는 멈추지 않고 다음 사진으로 넘어감
        try:
            result = process_photo(camera_id, photo, captured_at, SOURCE_AUTO_CAPTURE, default_zone_no)
        except Exception:
            log.exception("[%s] 자동 촬영 사진 처리 오류", camera_id)
            result = {"camera_id": camera_id, "status": "처리 오류", "violations": []}
        # 처리 결과를 카메라 화면 쪽에 알려줌
        if on_done:
            on_done(result)


# 처리 스레드를 처음 한 번만 시작하는 것을 담당함.
def _start_worker():
    global _worker_thread
    if _worker_thread is None:
        _worker_thread = threading.Thread(target=_process_loop, name="capture-worker", daemon=True)
        _worker_thread.start()


# 자동 촬영한 사진을 처리 대기열에 넣는 것을 담당함.
def submit_capture(camera_id, photo, captured_at, default_zone_no=None, on_done=None):
    """on_done(result): 처리가 끝나면 호출된다."""
    _start_worker()
    # 처리가 밀려 있으면 로그로 알림
    if _capture_queue.qsize() >= 3:
        log.warning("자동 촬영 사진 처리가 밀려 있음 (대기 %d장)", _capture_queue.qsize())
    _capture_queue.put((camera_id, photo, captured_at, default_zone_no, on_done))
