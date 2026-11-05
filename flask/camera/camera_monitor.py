"""카메라 한 대의 실시간 관제: 최신 프레임 → 자동 촬영 판단 → 차량 표시 → 화면(JPEG) 갱신."""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2

import config
from ai.fire_truck import mark_fire_trucks
from ai.parking import STATUS_VIOLATION
from ai.vehicle import detectVehicle
from camera.auto_capture import STATE_WAITING, AutoCapture
from camera.capture_worker import submit_capture
from camera.frame_reader import CameraFrameReader
from camera.overlay import draw_live_overlay, zone_display_name
from enforcement.photo_analyzer import find_zone_for_view
from utils.violation_log import write_undecidable

log = logging.getLogger(__name__)


# 실시간 화면용으로 프레임을 줄이는 것을 담당함.
def _shrink_for_live_view(frame):
    """반환: (줄인 화면, 배율). 이미 작으면 그대로 (배율 1)."""
    frame_width = frame.shape[1]
    if not config.LIVE_VIEW_WIDTH or frame_width <= config.LIVE_VIEW_WIDTH:
        return frame, 1.0
    scale = config.LIVE_VIEW_WIDTH / frame_width
    return cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), scale


# 원본 크기 기준 박스를 줄인 화면 좌표로 바꾸는 것을 담당함.
def _scale_box(box, scale):
    return tuple(int(value * scale) for value in box)


# 원본 크기 기준 점들(구역 테두리)을 줄인 화면 좌표로 바꾸는 것을 담당함.
def _scale_points(points, scale):
    if not points:
        return points
    return [[point[0] * scale, point[1] * scale] for point in points]


# 화면 표시용 구역의 흔들림을 줄이는 것을 담당함.
def _smooth_zone_polygon(previous_zone, new_polygon, frame_width):
    """직전 구역과 꼭짓점이 가까우면 중간 위치로 부드럽게 옮기고, 많이 다르면(드론이 크게 움직임) 새 위치를 그대로 씀."""
    if not previous_zone or len(previous_zone[0]) != len(new_polygon):
        return new_polygon
    previous_polygon = previous_zone[0]
    largest_move = max(abs(new[0] - old[0]) + abs(new[1] - old[1]) for new, old in zip(new_polygon, previous_polygon))
    if largest_move > frame_width * config.LIVE_ZONE_SMOOTH_MAX_MOVE_RATIO:
        return new_polygon
    weight = config.LIVE_ZONE_SMOOTH_NEW_WEIGHT
    return [[old[0] + (new[0] - old[0]) * weight, old[1] + (new[1] - old[1]) * weight]
            for new, old in zip(new_polygon, previous_polygon)]


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
        # 움직이는 중에도 보여줄 구역 (줄인 화면 좌표의 테두리, 구역번호, 찾은 시각). 판정에는 쓰지 않음
        self._live_zone = None
        self._live_zone_busy = False
        self._last_live_zone_at = 0.0
        self._live_zone_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"live-zone-{camera_id}")

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

        # 실시간 화면은 작게 줄여서 처리 (4K 영상도 화면이 느려지지 않게). 촬영 사진은 위에서 원본 크기 그대로 씀
        preview, preview_scale = _shrink_for_live_view(frame)

        # 2. 실시간 화면용 차량 탐지 (CPU를 아끼려고 일정 간격으로만, 줄인 화면으로)
        if now - self._last_live_detect_at >= config.LIVE_DETECT_INTERVAL_SECONDS:
            self._last_live_detect_at = now
            self._live_vehicles = self._detect_for_live_view(preview)

        # 3. 움직이는 중에도 구역을 보여주려고 일정 간격으로 구역을 찾음 (별도 작업이라 화면이 멈추지 않음)
        self._request_live_zone(preview, now)

        # 4. 화면 그리기 → JPEG (촬영 결과의 좌표는 원본 크기 기준이라 줄인 화면에 맞게 바꿈)
        zone_polygon, zone_no = self._last_zone_to_draw()
        zone_polygon = _scale_points(zone_polygon, preview_scale)
        if not zone_polygon:
            zone_polygon, zone_no = self._recent_live_zone(now)
        live_image = draw_live_overlay(
            preview, self._live_vehicles, zone_polygon, zone_no,
            self.auto_capture.state, self.auto_capture.still_seconds, *self._last_result_line(),
            [(_scale_box(box, preview_scale), number) for box, number in self._last_violations()],
            [(_scale_box(box, preview_scale), number) for box, number in self._last_zone_cars()])
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

    # 화면 표시용 구역 찾기를 일정 간격으로 별도 작업에 맡기는 것을 담당함.
    def _request_live_zone(self, preview, now):
        if (not config.LIVE_ZONE_INTERVAL_SECONDS or self._live_zone_busy
                or now - self._last_live_zone_at < config.LIVE_ZONE_INTERVAL_SECONDS):
            return
        self._live_zone_busy, self._last_live_zone_at = True, now
        # 매번 새 스레드를 만들면 모델 라이브러리가 스레드마다 메모리를 잡고 놓지 않아 메모리가 계속 늘어남 → 스레드 하나를 재사용
        self._live_zone_executor.submit(self._find_live_zone, preview.copy(), list(self._live_vehicles), now)

    # 줄인 화면에서 구역을 찾아 기억하는 것을 담당함 (별도 작업에서 실행).
    def _find_live_zone(self, preview, vehicles, found_at):
        try:
            found = find_zone_for_view(self.camera_id, preview, vehicles, self.default_zone_no)
            if found is None:
                return
            polygon, zone_no = _smooth_zone_polygon(self._live_zone, found[0], preview.shape[1]), found[1]
            self._live_zone = (polygon, zone_no, found_at)
        except Exception:
            log.exception("[%s] 화면 표시용 구역 찾기 오류", self.camera_id)
        finally:
            self._live_zone_busy = False

    # 최근에 찾은 화면 표시용 구역을 돌려주는 것을 담당함 (오래되면 위치가 안 맞으니 안 그림).
    def _recent_live_zone(self, now):
        live_zone = self._live_zone
        if live_zone and now - live_zone[2] <= config.LIVE_ZONE_MAX_AGE_SECONDS:
            return live_zone[0], live_zone[1]
        return None, None

    # 화면에 빨간 테두리와 차량번호로 표시할 위반 차량을 고르는 것을 담당함.
    def _last_violations(self):
        """반환: [(box, 차량번호)]"""
        # 구역과 같이, 마지막 촬영 장면이 그대로일 때만 표시 (화면이 바뀌면 위치가 맞지 않음)
        if self.last_result and self.auto_capture.state == STATE_WAITING:
            return [(violation["box"], violation["car_number"])
                    for violation in self.last_result.get("violations", []) if violation.get("box")]
        return []

    # 화면에 주황 테두리와 읽은 번호로 표시할 구역 안 차량(위반 확정 제외)을 고르는 것을 담당함.
    def _last_zone_cars(self):
        """반환: [(box, 차량번호 또는 None)]"""
        # 위반과 같이, 마지막 촬영 장면이 그대로일 때만 표시 (화면이 바뀌면 위치가 맞지 않음)
        if self.last_result and self.auto_capture.state == STATE_WAITING:
            return [(car["box"], car["car_number"]) for car in self.last_result.get("cars", [])
                    if car.get("box") and car.get("status") != STATUS_VIOLATION]
        return []

    # 화면에 쓸 마지막 처리 결과 한 줄을 만드는 것을 담당함.
    def _last_result_line(self):
        if not self.last_result:
            return "", False
        violation_count = len(self.last_result.get("violations", []))
        zone_no = zone_display_name(self.last_result["zone_no"]) if self.last_result.get("zone_no") else "-"
        # 위반이 있으면 빨간 글자로 차량 수 표시
        if violation_count:
            return f"LAST {self.last_result.get('captured_at', '')[-8:]} {zone_no}: VIOLATION x{violation_count}", True
        car_count = len(self.last_result.get("cars", []))
        return f"LAST {self.last_result.get('captured_at', '')[-8:]} {zone_no}: cars in zone {car_count}", False

    # 초당 처리 화면 수(FPS) 계산을 담당함.
    def _update_fps(self, elapsed_seconds):
        current_fps = 1 / elapsed_seconds if elapsed_seconds > 0 else 0
        self.fps = 0.9 * self.fps + 0.1 * current_fps   # 부드럽게 평균
