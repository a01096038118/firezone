"""실시간 모니터링 시작점 (MON-001): config.CAMERAS 의 카메라마다 CameraMonitor 를 띄운다."""
import logging
import time

from ai.plate_reader import start_plate_reader_warmup
from ai.vehicle import warmup_vehicle_model
from camera.camera_config import load_camera_config
from camera.camera_monitor import CameraMonitor

log = logging.getLogger(__name__)

# 카메라 ID → CameraMonitor
_camera_monitors = {}


# AI 모델을 미리 불러두는 것(워밍업)을 담당함.
def _warmup_models():
    # 번호판 OCR은 별도 프로세스에서 미리 불러둠 (기다리지 않음)
    start_plate_reader_warmup()
    # 차량 탐지 모델은 여기서 불러둠
    warmup_started_at = time.time()
    try:
        warmup_vehicle_model()
        log.info("차량 탐지 모델 워밍업 완료 (%.1f초)", time.time() - warmup_started_at)
    except Exception:
        log.exception("차량 탐지 모델 워밍업 실패 (첫 분석이 느릴 수 있음)")


# 설정된 카메라마다 실시간 관제를 시작하는 것을 담당함.
def monitoring():
    """앱 시작 시 한 번 호출. 이미 시작된 카메라는 다시 시작하지 않는다."""
    _warmup_models()
    for camera_id, camera_settings in load_camera_config().items():
        # 꺼둔 카메라나 이미 시작한 카메라는 건너뜀
        if not camera_settings.get("enabled", True) or camera_id in _camera_monitors:
            continue
        camera_monitor = CameraMonitor(camera_id, camera_settings)
        camera_monitor.start()
        _camera_monitors[camera_id] = camera_monitor
        log.info("[%s] 모니터링 시작 (%s)", camera_id, camera_settings["source"])


# 카메라 ID 로 실시간 관제 객체를 찾는 것을 담당함.
def get_camera_monitor(camera_id):
    return _camera_monitors.get(camera_id)


# 모든 카메라의 상태 목록을 만드는 것을 담당함.
def get_all_camera_status():
    return [camera_monitor.get_status() for camera_monitor in _camera_monitors.values()]
