"""카메라(ESP32-CAM)에서 최신 프레임 읽기. 분석이 느려도 항상 가장 최근 화면을 쓰도록 별도 스레드에서 읽는다."""
import logging
import threading
import time

import cv2

import config
from camera.camera_config import parse_video_source

log = logging.getLogger(__name__)


# 카메라 한 대에서 최신 프레임을 계속 읽어두는 것을 담당함.
class CameraFrameReader(threading.Thread):
    # 카메라 주소와 최신 프레임 보관 자리를 준비하는 것을 담당함.
    def __init__(self, camera_id, source):
        super().__init__(name=f"reader-{camera_id}", daemon=True)
        self.camera_id = camera_id
        self.video_source, self.is_video_file = parse_video_source(source)
        self.is_connected = False
        self._latest_frame = None
        self._frame_count = 0            # 새 프레임이 들어왔는지 구분하는 번호
        self._frame_lock = threading.Lock()

    # 가장 최근 프레임과 그 번호를 꺼내는 것을 담당함.
    def get_latest_frame(self):
        with self._frame_lock:
            return self._frame_count, self._latest_frame

    # 카메라를 열고 프레임을 계속 읽으며, 끊기면 다시 연결하는 것을 담당함.
    def run(self):
        while True:
            # 카메라 연결
            capture = cv2.VideoCapture(self.video_source)
            if not capture.isOpened():
                self.is_connected = False
                log.warning("[%s] 카메라 연결 실패: %s (%d초 뒤 재시도)",
                            self.camera_id, self.video_source, config.CAMERA_RECONNECT_WAIT_SECONDS)
                time.sleep(config.CAMERA_RECONNECT_WAIT_SECONDS)
                continue
            self.is_connected = True
            log.info("[%s] 카메라 연결됨: %s", self.camera_id, self.video_source)
            # 영상 파일은 실제 속도로 재생하기 위해 프레임 간격을 계산
            frame_interval = 1 / (capture.get(cv2.CAP_PROP_FPS) or 30) if self.is_video_file else 0

            # 프레임 읽기 반복
            while True:
                read_success, frame = capture.read()
                if not read_success:
                    # 영상 파일이 끝나면 처음부터 다시 재생
                    if self.is_video_file:
                        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    log.warning("[%s] 영상 수신 중단 → 다시 연결", self.camera_id)
                    break
                with self._frame_lock:
                    self._latest_frame = frame
                    self._frame_count += 1
                if frame_interval:
                    time.sleep(frame_interval)

            capture.release()
            self.is_connected = False
            time.sleep(config.CAMERA_RECONNECT_WAIT_SECONDS)
