"""번호판 OCR 실행 관리.

OCR은 CPU를 많이 써서, 같은 프로세스에서 돌리면 실시간 화면이 OCR이 끝날 때까지 멈춘다.
(측정: 평소 프레임 0.2초 → OCR 도중 12초)
그래서 OCR은 별도 프로세스 1개에서만 실행한다.
"""
import logging
import time
from concurrent.futures import ProcessPoolExecutor

from ai.plate import recognizeLicensePlate, warmup_plate_reader

log = logging.getLogger(__name__)

_plate_reader_process = None   # 처음 쓸 때 만든다


# 번호판 인식 전용 프로세스를 처음 한 번만 만드는 것을 담당함.
def _get_plate_reader_process():
    global _plate_reader_process
    if _plate_reader_process is None:
        _plate_reader_process = ProcessPoolExecutor(max_workers=1)
    return _plate_reader_process


# 차량 이미지 한 장의 번호판을 전용 프로세스에서 읽고 결과를 기다리는 것을 담당함.
def read_plate_and_wait(vehicle_image):
    """차량번호(예: "12가3456") 또는 None. 오류가 나도 None 을 돌려주고 로그를 남긴다."""
    try:
        # 전용 프로세스에 맡기고 끝날 때까지 기다림
        return _get_plate_reader_process().submit(recognizeLicensePlate, vehicle_image).result()
    except Exception:
        log.exception("번호판 인식 오류")
        return None


# 번호판 인식 프로세스를 미리 띄우고 OCR을 불러두는 것(워밍업)을 담당함.
def start_plate_reader_warmup():
    """서버 시작은 기다리지 않는다. 끝나면 소요 시간을 로그로 남긴다."""
    warmup_started_at = time.time()

    # 워밍업이 끝났을 때 결과를 로그로 남기는 것을 담당함.
    def on_warmup_done(finished_job):
        try:
            finished_job.result()
            log.info("번호판 인식 워밍업 완료 (%.1f초)", time.time() - warmup_started_at)
        except Exception:
            log.exception("번호판 인식 워밍업 실패 (첫 번호판 인식이 느릴 수 있음)")

    log.info("번호판 인식 워밍업 시작 (별도 프로세스)")
    _get_plate_reader_process().submit(warmup_plate_reader).add_done_callback(on_warmup_done)
