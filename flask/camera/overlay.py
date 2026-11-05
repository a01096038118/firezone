"""실시간 화면 표시: 차량 박스, 구역 테두리, 위반 차량, 자동 촬영 상태 글자를 그린다.

OpenCV는 한글을 못 그려서 화면 글자는 영어로 표시한다 (차량번호만 Pillow 로 그림).
마지막 촬영 장면이 그대로일 때: 구역 안 차량은 주황 박스 + 읽은 번호, 위반 확정 차량은 빨간 박스 + 번호.
선 굵기·글자 크기는 화면 가로 크기에 맞춰 키운다 (4K 영상에서도 잘 보이게).
"""
import os
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
from camera.auto_capture import STATE_MOVING, STATE_STILL, STATE_WAITING

# 차량번호(한글)용 글꼴 후보 (Windows 맑은 고딕 → 없으면 기본 글꼴)
KOREAN_FONT_PATHS = ("C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf",
                     "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")

# 화면 표시 색 (OpenCV는 BGR 순서)
COLOR_VEHICLE = (0, 200, 0)        # 초록: 일반 차량
COLOR_FIRE_TRUCK = (255, 120, 0)   # 파랑: 소방차 (위반 아님)
COLOR_ZONE_LINE = (0, 200, 255)    # 노랑: 구역 테두리 (마지막 촬영에서 찾은 위치)
COLOR_VIOLATION = (0, 0, 255)      # 빨강: 위반 차량
COLOR_ZONE_CAR = (0, 140, 255)     # 주황: 구역 안 차량 (번호판 확인 중, 아직 위반 아님)
# 차량번호 글자 바탕색 (Pillow 는 RGB 순서)
LABEL_RGB_VIOLATION = (255, 0, 0)
LABEL_RGB_ZONE_CAR = (255, 140, 0)
LABEL_UNREADABLE = "번호판 미인식"
COLOR_STATUS_BACKGROUND = (0, 0, 0)
COLOR_STATUS_TEXT = (255, 255, 255)
COLOR_VIOLATION_TEXT = (0, 0, 255)

# 이 가로 크기에서 굵기·글자 크기 1배 (더 큰 화면은 비례해서 키움)
BASE_WIDTH = 1280

# 자동 촬영 상태 → 화면 글자
STATE_LABELS = {STATE_MOVING: "MOVING", STATE_STILL: "STILL", STATE_WAITING: "CAPTURED - waiting for next scene"}


# 화면 크기에 맞는 배율을 구하는 것을 담당함.
def _scale(canvas):
    return max(1.0, canvas.shape[1] / BASE_WIDTH)


# 차량 박스를 그리는 것을 담당함.
def draw_vehicles(canvas, vehicles):
    scale = _scale(canvas)
    for vehicle in vehicles:
        x1, y1, x2, y2 = vehicle["box"]
        # 소방차는 파랑, 나머지는 초록
        if vehicle.get("is_fire_truck"):
            box_color, label = COLOR_FIRE_TRUCK, "FIRE TRUCK"
        else:
            box_color, label = COLOR_VEHICLE, vehicle["vehicle_type"]
        # 일반 차량은 얇게(1px) 그려서 구역 안 차량(주황)·위반 차량(빨강)이 더 눈에 띄게 함
        cv2.rectangle(canvas, (x1, y1), (x2, y2), box_color, max(1, int(1 * scale)))
        cv2.putText(canvas, label, (x1, max(y1 - int(6 * scale), int(14 * scale))),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5 * scale, box_color, int(2 * scale))


# 마지막 촬영에서 찾은 구역 테두리를 그리는 것을 담당함.
def draw_zone(canvas, zone_polygon, zone_no):
    if not zone_polygon:
        return
    scale = _scale(canvas)
    points = np.array(zone_polygon, dtype=np.int32)
    _fill_zone(canvas, points)
    cv2.polylines(canvas, [points], True, COLOR_ZONE_LINE, int(3 * scale))
    _draw_zone_label(canvas, zone_no, scale)


# 구역 안을 반투명하게 칠하는 것을 담당함 (구역을 둘러싼 부분만 섞어서 빠르게).
def _fill_zone(canvas, points):
    if config.ZONE_FILL_OPACITY <= 0:
        return
    canvas_height, canvas_width = canvas.shape[:2]
    left, top = max(int(points[:, 0].min()), 0), max(int(points[:, 1].min()), 0)
    right, bottom = min(int(points[:, 0].max()) + 1, canvas_width), min(int(points[:, 1].max()) + 1, canvas_height)
    if right <= left or bottom <= top:
        return
    region = canvas[top:bottom, left:right]
    mask = np.zeros(region.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [points - (left, top)], 255)
    tinted = cv2.addWeighted(region, 1 - config.ZONE_FILL_OPACITY,
                             np.full_like(region, COLOR_ZONE_LINE), config.ZONE_FILL_OPACITY, 0)
    region[mask > 0] = tinted[mask > 0]


# 구역번호를 화면 표시용 이름으로 바꾸는 것을 담당함. 예: "1" → "zone_01", "AUTO" → "zone_AUTO"
def zone_display_name(zone_no):
    zone_text = str(zone_no or "")
    return f"zone_{int(zone_text):02d}" if zone_text.isdigit() else f"zone_{zone_text}"


# 화면 오른쪽 위에 구역 이름(zone_01)을 검은 띠 위 노란 글자로 쓰는 것을 담당함.
def _draw_zone_label(canvas, zone_no, scale):
    if not zone_no:
        return
    text = zone_display_name(zone_no)
    font_scale, thickness = 0.8 * scale, int(2 * scale)
    (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    margin = int(10 * scale)
    right, top = canvas.shape[1] - margin, margin
    cv2.rectangle(canvas, (right - text_width - margin, top), (right, top + text_height + margin),
                  COLOR_STATUS_BACKGROUND, -1)
    cv2.putText(canvas, text, (right - text_width - margin // 2, top + text_height + margin // 2),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLOR_ZONE_LINE, thickness)


# 차량번호(한글) 글자 그림을 만드는 것을 담당함 (같은 번호는 한 번만 만들어 재사용).
@lru_cache(maxsize=64)
def _plate_label_image(car_number, font_size, background_rgb=LABEL_RGB_VIOLATION):
    """반환: 색 바탕(기본 빨강)에 흰 차량번호가 쓰인 BGR 이미지"""
    font_path = next((path for path in KOREAN_FONT_PATHS if os.path.exists(path)), None)
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    left, top, right, bottom = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), car_number, font=font)
    padding = max(2, font_size // 6)
    label = Image.new("RGB", (right - left + padding * 2, bottom - top + padding * 2), background_rgb)
    ImageDraw.Draw(label).text((padding - left, padding - top), car_number, font=font, fill=(255, 255, 255))
    return cv2.cvtColor(np.array(label), cv2.COLOR_RGB2BGR)


# 위반 차량을 빨간 테두리(일반 차량 박스와 같은 굵기)와 차량번호로 표시하는 것을 담당함.
def draw_violations(canvas, violations):
    """violations: [(box, 차량번호)]"""
    scale = _scale(canvas)
    canvas_height, canvas_width = canvas.shape[:2]
    for box, car_number in violations:
        _draw_box_with_number(canvas, box, car_number or "VIOLATION", COLOR_VIOLATION, LABEL_RGB_VIOLATION, scale,
                              canvas_width, canvas_height)


# 구역 안 차량(아직 위반 아님)을 주황 테두리와 읽은 번호로 표시하는 것을 담당함.
def draw_zone_cars(canvas, zone_cars):
    """zone_cars: [(box, 차량번호 또는 None)]. 번호를 못 읽었으면 "번호판 미인식"으로 표시."""
    scale = _scale(canvas)
    canvas_height, canvas_width = canvas.shape[:2]
    for box, car_number in zone_cars:
        _draw_box_with_number(canvas, box, car_number or LABEL_UNREADABLE, COLOR_ZONE_CAR, LABEL_RGB_ZONE_CAR, scale,
                              canvas_width, canvas_height)


# 박스 테두리와 그 위의 차량번호 글자를 그리는 것을 담당함.
def _draw_box_with_number(canvas, box, text, box_color, label_rgb, scale, canvas_width, canvas_height):
    x1, y1, x2, y2 = box
    # 1. 테두리 (초록 박스와 같은 굵기)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), box_color, int(2 * scale))
    # 2. 박스 바로 위에 차량번호 (색 바탕 흰 글자). 화면 위쪽에 붙으면 박스 안쪽 위에 표시
    label = _plate_label_image(text, int(18 * scale), label_rgb)
    label_height, label_width = label.shape[:2]
    label_top = y1 - label_height if y1 - label_height >= 0 else y1
    label_left = min(max(x1, 0), canvas_width - label_width)
    if label_left < 0 or label_top + label_height > canvas_height:
        return
    canvas[label_top:label_top + label_height, label_left:label_left + label_width] = label


# 왼쪽 위에 자동 촬영 상태와 마지막 결과를 쓰는 것을 담당함.
def draw_status(canvas, capture_state, still_seconds, last_result_line, has_violation):
    scale = _scale(canvas)
    state_text = STATE_LABELS.get(capture_state, capture_state)
    # 멈춤 확인 중이면 몇 초째 멈춰 있는지 표시
    if capture_state == STATE_STILL:
        state_text = f"STILL {still_seconds:.1f}s"
    lines = [(f"AUTO CAPTURE: {state_text}", COLOR_STATUS_TEXT)]
    if last_result_line:
        lines.append((last_result_line, COLOR_VIOLATION_TEXT if has_violation else COLOR_STATUS_TEXT))

    # 검은 띠 위에 흰 글자 (어느 배경에서도 보이게)
    font_scale, thickness = 0.6 * scale, int(2 * scale)
    for line_index, (text, text_color) in enumerate(lines):
        y = int((24 + line_index * 26) * scale)
        (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        cv2.rectangle(canvas, (int(6 * scale), y - int(19 * scale)), (int(14 * scale) + text_width, y + int(7 * scale)),
                      COLOR_STATUS_BACKGROUND, -1)
        cv2.putText(canvas, text, (int(10 * scale), y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)


# 실시간 화면 한 장을 만드는 것을 담당함.
def draw_live_overlay(frame, vehicles, zone_polygon, zone_no, capture_state, still_seconds,
                      last_result_line, has_violation, violations=(), zone_cars=()):
    """원본 프레임은 그대로 두고, 그린 복사본을 돌려준다.
    violations: [(box, 차량번호)] 위반 확정 / zone_cars: [(box, 차량번호 또는 None)] 구역 안 차량"""
    canvas = frame.copy()
    draw_zone(canvas, zone_polygon, zone_no)
    draw_vehicles(canvas, vehicles)
    # 구역 안 차량 → 위반 차량 순서로 일반 차량 박스 위에 덮어 그림
    draw_zone_cars(canvas, zone_cars)
    draw_violations(canvas, violations)
    draw_status(canvas, capture_state, still_seconds, last_result_line, has_violation)
    return canvas
