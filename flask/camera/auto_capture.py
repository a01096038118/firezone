"""자동 촬영: 화면이 바뀐 뒤 STILL_SECONDS_BEFORE_CAPTURE 초 동안 멈춰 있으면 가장 선명한 장면을 찍는다.

드론이 이동(화면이 움직임) → 호버링(화면이 멈춤) → 촬영 → 다시 이동 하는 흐름과 같다.
한 번 찍은 뒤에는 화면이 다시 바뀔 때까지 찍지 않는다 (같은 장면을 여러 번 찍지 않음).
"""
import cv2

import config

# 화면 변화 비교용 작은 크기 (빠르고, 작은 흔들림·잡음에 덜 민감함)
COMPARE_SIZE = (160, 90)
# 선명도 계산용 크기
SHARPNESS_WIDTH = 640

STATE_MOVING = "화면 바뀌는 중"
STATE_STILL = "멈춤 확인 중"
STATE_WAITING = "촬영 완료, 다음 화면 대기"


# 화면을 비교용으로 작게 줄이고 흑백으로 바꾸는 것을 담당함.
def _to_compare_image(frame):
    small = cv2.resize(frame, COMPARE_SIZE)
    return cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)


# 화면이 얼마나 선명한지 계산하는 것을 담당함.
def measure_sharpness(frame):
    """값이 클수록 선명함 (윤곽선이 또렷할수록 커지는 라플라시안 분산)."""
    scale = SHARPNESS_WIDTH / frame.shape[1]
    gray = cv2.cvtColor(cv2.resize(frame, None, fx=scale, fy=scale), cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# 카메라 한 대의 자동 촬영 판단을 담당함.
class AutoCapture:
    # 처음 상태를 준비하는 것을 담당함.
    def __init__(self):
        self._previous_compare_image = None
        self._still_since = None
        self._has_new_scene = True        # 처음 들어온 장면도 찍을 수 있게 True 로 시작
        self._best_frame = None
        self._best_sharpness = -1.0
        self.state = STATE_MOVING
        self.still_seconds = 0.0

    # 새 프레임을 보고 지금 찍어야 하면 (사진, 선명도) 를 돌려주는 것을 담당함.
    def feed(self, frame, now):
        """찍을 때가 아니면 None."""
        compare_image = _to_compare_image(frame)
        previous_image, self._previous_compare_image = self._previous_compare_image, compare_image
        if previous_image is None:
            return None

        # 1. 이전 화면과 차이가 크면 "움직이는 중" → 멈춤 시간과 후보를 초기화
        scene_difference = cv2.absdiff(compare_image, previous_image).mean()
        if scene_difference > config.SCENE_CHANGE_THRESHOLD:
            self._reset_still(new_scene=True)
            return None

        # 2. 너무 어두운 화면(꺼진 화면, 사진 전환 중)은 찍지 않음
        if compare_image.mean() < config.MIN_PHOTO_BRIGHTNESS:
            self._reset_still(new_scene=self._has_new_scene)
            return None

        # 3. 이미 찍은 장면이면 다음 장면까지 기다림
        if not self._has_new_scene:
            self.state = STATE_WAITING
            return None

        # 4. 멈춘 동안 가장 선명한 프레임을 후보로 기억
        if self._still_since is None:
            self._still_since = now
        self.state, self.still_seconds = STATE_STILL, now - self._still_since
        sharpness = measure_sharpness(frame)
        if sharpness > self._best_sharpness:
            self._best_frame, self._best_sharpness = frame.copy(), sharpness

        # 5. 충분히 멈춰 있었으면 가장 선명한 프레임으로 촬영
        if self.still_seconds >= config.STILL_SECONDS_BEFORE_CAPTURE:
            captured = (self._best_frame, self._best_sharpness)
            self._reset_still(new_scene=False)
            self.state = STATE_WAITING
            return captured
        return None

    # 멈춤 시간과 선명한 프레임 후보를 지우는 것을 담당함.
    def _reset_still(self, new_scene):
        self._still_since = None
        self._best_frame, self._best_sharpness = None, -1.0
        self.still_seconds = 0.0
        if new_scene:
            self._has_new_scene = True
            self.state = STATE_MOVING
        else:
            self._has_new_scene = False
