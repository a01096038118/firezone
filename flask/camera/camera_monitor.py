"""카메라 한 대의 실시간 관제: 최신 프레임 → 자동 촬영 판단 → 차량 표시 → 화면(JPEG) 갱신."""
import logging
import threading
import time

import cv2

import config
from ai.fire_truck import mark_fire_trucks
from ai.vehicle import detectVehicle
from camera.auto_capture import STATE_WAITING, AutoCapture
from camera.capture_worker import submit_capture
from camera.frame_reader import CameraFrameReader
from camera.overlay import draw_live_overlay
from utils.violation_log import write_undecidable

log = logging.getLogger(__name__)


# 카메라 한 대의 실시간 관제 전체를 담당함.
class CameraMonitor(threading.Thread):
    # 카메라 정보, 프레임 읽기, 자동 촬영 준비를 담당함.
    def __init__(self, camera_id, camera_settings):
        super().__init__(name=f"monitor-{camera_id}", daemon=True)
        self.camera_id = camera_id
        self.camera_name = camera_settings.get("name", camera_id)
        self.default_zone_no = camera_settings.get("default_zone")
        self.frame_reader = CameraFrameReader(camera_id, camera_settings["source"])
        self.auto_capture = AutoCapture()
        self.latest_jpeg = None             # 관제 화면으로 보낼 최신 화면 (JPEG)
        self.fps = 0.0                      # 초당 처리 화면 수
        self.detection_failed = False       # 차량 탐지 모델 오류 여부
        self.last_result = None             # 마지막 자동 촬영 처리 결과
        self._live_vehicles = []
        self._last_live_detect_at = 0.0

    # 카메라 연결 상태와 자동 촬영 상태 정보를 만드는 것을 담당함.
    def get_status(self):
        return {
            "camera_id": self.camera_id,
            "name": self.camera_name,
            "connected": self.frame_reader.is_connected,
            "fps": round(self.fps, 1),
            "detection_failed": self.detection_failed,
            "auto_capture_state": self.auto_capture.state,
            "last_result": self.last_result,
            "stream_url": f"{config.FLASK_PUBLIC_URL}/api/monitor/{self.camera_id}",
        }

    # 새 프레임이 들어올 때마다 화면을 갱신하는 것을 반복하는 것을 담당함.
    def run(self):
        self.frame_reader.start()
        last_frame_count = 0
        while True:
            # 새 프레임이 없으면 잠깐 기다림
            frame_count, frame = self.frame_reader.get_latest_frame()
            if frame is None or frame_count == last_frame_count:
                time.sleep(0.01)
                continue
            last_frame_count = frame_count

            started_at = time.time()
            try:
                self._handle_frame(frame, started_at)
            except Exception:
                log.exception("[%s] 화면 처리 오류", self.camera_id)
            self._update_fps(time.time() - started_at)

    # 프레임 한 장의 처리 순서(자동 촬영 → 차량 표시 → 화면 그리기)를 담당함.
    def _handle_frame(self, frame, now):
        # 1. 자동 촬영 판단 (화면이 멈추면 가장 선명한 장면을 찍음)
        captured = self.auto_capture.feed(frame, now)
        if captured is not None:
            self._on_captured(*captured, now)

        # 2. 실시간 화면용 차량 탐지 (CPU를 아끼려고 일정 간격으로만)
        if now - self._last_live_detect_at >= config.LIVE_DETECT_INTERVAL_SECONDS:
            self._last_live_detect_at = now
            self._live_vehicles = self._detect_for_live_view(frame)

        # 3. 화면 그리기 → JPEG
        live_image = draw_live_overlay(frame, self._live_vehicles, *self._last_zone_to_draw(),
                                       self.auto_capture.state, self.auto_capture.still_seconds,
                                       *self._last_result_line())
        encode_success, jpeg_buffer = cv2.imencode(".jpg", live_image)
        if encode_success:
            self.latest_jpeg = jpeg_buffer.tobytes()

    # 자동 촬영된 사진을 확인하고 단속 처리 대기열에 넣는 것을 담당함.
    def _on_captured(self, photo, sharpness, captured_at):
        # 흐린 사진은 판정 불가로 기록하고 처리하지 않음
        if sharpness < config.MIN_PHOTO_SHARPNESS:
            write_undecidable("사진 흐림", self.camera_id, captured_at, detail=f"선명도 {sharpness:.0f}")
            log.info("[%s] 자동 촬영: 사진이 흐려서 판정 불가 (선명도 %.0f)", self.camera_id, sharpness)
            return
        log.info("[%s] 자동 촬영 (선명도 %.0f) → 단속 처리 대기열", self.camera_id, sharpness)
        submit_capture(self.camera_id, photo, captured_at, self.default_zone_no, on_done=self._on_processed)

    # 단속 처리가 끝난 결과를 기억하는 것을 담당함.
    def _on_processed(self, result):
        self.last_result = result

    # 실시간 화면에 표시할 차량을 찾는 것을 담당함.
    def _detect_for_live_view(self, frame):
        try:
            vehicles = detectVehicle(frame)
            mark_fire_trucks(frame, vehicles)
            self.detection_failed = False
            return vehicles
        except Exception:
            # 모델 오류는 상태로 알리고 화면은 계속 보여줌 (MON-002 탐지 실패 상태)
            if not self.detection_failed:
                log.exception("[%s] 실시간 차량 탐지 실패", self.camera_id)
            self.detection_failed = True
            return []

    # 화면에 그릴 구역 테두리를 고르는 것을 담당함.
    def _last_zone_to_draw(self):
        # 마지막 촬영 장면이 그대로일 때만 그 촬영에서 찾은 구역을 그림
        if self.last_result and self.auto_capture.state == STATE_WAITING:
            return self.last_result.get("zone_polygon"), self.last_result.get("zone_no")
        return None, None

    # 화면에 쓸 마지막 처리 결과 한 줄을 만드는 것을 담당함.
    def _last_result_line(self):
        if not self.last_result:
            return "", False
        violation_count = len(self.last_result.get("violations", []))
        zone_no = self.last_result.get("zone_no") or "-"
        # 위반이 있으면 빨간 글자로 차량 수 표시
        if violation_count:
            return f"LAST {self.last_result.get('captured_at', '')[-8:]} {zone_no}: VIOLATION x{violation_count}", True
        car_count = len(self.last_result.get("cars", []))
        return f"LAST {self.last_result.get('captured_at', '')[-8:]} {zone_no}: cars in zone {car_count}", False

    # 초당 처리 화면 수(FPS) 계산을 담당함.
    def _update_fps(self, elapsed_seconds):
        current_fps = 1 / elapsed_seconds if elapsed_seconds > 0 else 0
        self.fps = 0.9 * self.fps + 0.1 * current_fps   # 부드럽게 평균
