"""카메라(ESP32-CAM)에서 최신 프레임 읽기. 분석이 느려도 항상 가장 최근 화면을 쓰도록 별도 스레드에서 읽는다."""
import logging
import os
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

    # 카메라 주소에 맞는 방식으로 카메라를 여는 것을 담당함.
    # 웹캠(번호)은 Windows 기본 방식(MSMF)으로 열면 Osmo Pocket 등이 검은 화면만 보내서 DirectShow 로 열고 해상도를 지정함
    def _open_capture(self):
        if isinstance(self.video_source, int) and os.name == "nt":
            capture = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_WIDTH)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_HEIGHT)
            return capture
        return cv2.VideoCapture(self.video_source)

    # 카메라를 열고 프레임을 계속 읽으며, 끊기면 다시 연결하는 것을 담당함.
    def run(self):
        while True:
            # 카메라 연결
            capture = self._open_capture()
            if not capture.isOpened():
                self.is_connected = False
                log.warning("[%s] 카메라 연결 실패: %s (%d초 뒤 재시도)",
                            self.camera_id, self.video_source, config.CAMERA_RECONNECT_WAIT_SECONDS)
                time.sleep(config.CAMERA_RECONNECT_WAIT_SECONDS)
                continue
            self.is_connected = True
            log.info("[%s] 카메라 연결됨: %s", self.camera_id, self.video_source)
            # 영상 파일은 실제 시간에 맞춰 재생 (처리가 늦으면 밀린 장면을 건너뛰어 원래 속도 유지)
            video_fps = (capture.get(cv2.CAP_PROP_FPS) or 30) if self.is_video_file else 0
            play_started_at, played_frames = time.time(), 0
            black_since = None      # 웹캠이 검은 화면만 보내기 시작한 시각

            # 프레임 읽기 반복
            while True:
                read_success, frame = capture.read()
                if not read_success:
                    # 영상 파일이 끝나면 처음부터 다시 재생
                    if self.is_video_file:
                        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        play_started_at, played_frames = time.time(), 0
                        continue
                    log.warning("[%s] 영상 수신 중단 → 다시 연결", self.camera_id)
                    break
                # 웹캠이 다시 연결된 뒤 검은 화면만 보내면 (Osmo Pocket 등) 끊고 새로 연결
                if isinstance(self.video_source, int):
                    if self._is_black(frame):
                        black_since = black_since or time.time()
                        if time.time() - black_since >= config.WEBCAM_BLACK_RECONNECT_SECONDS:
                            log.warning("[%s] 웹캠이 %d초 동안 검은 화면만 보냄 → 다시 연결",
                                        self.camera_id, config.WEBCAM_BLACK_RECONNECT_SECONDS)
                            break
                    else:
                        black_since = None
                with self._frame_lock:
                    self._latest_frame = frame
                    self._frame_count += 1
                if video_fps:
                    played_frames = self._keep_real_time(capture, video_fps, play_started_at, played_frames + 1)

            capture.release()
            self.is_connected = False
            time.sleep(config.CAMERA_RECONNECT_WAIT_SECONDS)

    # 화면이 거의 완전히 검은지 확인하는 것을 담당함. (작게 줄여서 평균 밝기만 봄)
    @staticmethod
    def _is_black(frame):
        small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
        return float(small.mean()) < config.WEBCAM_BLACK_MAX_BRIGHTNESS

    # 영상 파일을 실제 시간에 맞추는 것(늦으면 건너뛰고, 빠르면 기다림)을 담당함.
    def _keep_real_time(self, capture, video_fps, play_started_at, played_frames):
        """반환: 지금까지 지나간(읽거나 건너뛴) 프레임 수."""
        # 늦었으면 밀린 장면을 건너뜀 (grab 은 화면 변환을 안 해서 read 보다 가벼움). 한 번에 최대 1초 분량까지만
        behind_frames = int((time.time() - play_started_at) * video_fps) - played_frames
        for _ in range(min(max(behind_frames, 0), int(video_fps))):
            if not capture.grab():
                break
            played_frames += 1
        # 빠르면 원래 속도에 맞게 기다림
        wait_seconds = played_frames / video_fps - (time.time() - play_started_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        return played_frames
