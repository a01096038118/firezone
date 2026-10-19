"""실시간 화면 표시: 차량 박스, 구역 테두리, 자동 촬영 상태 글자를 그린다.

OpenCV는 한글을 못 그려서 화면 글자는 영어로 표시한다.
"""
import cv2
import numpy as np

from camera.auto_capture import STATE_MOVING, STATE_STILL, STATE_WAITING

# 화면 표시 색 (OpenCV는 BGR 순서)
COLOR_VEHICLE = (0, 200, 0)        # 초록: 일반 차량
COLOR_FIRE_TRUCK = (255, 120, 0)   # 파랑: 소방차 (위반 아님)
COLOR_ZONE_LINE = (0, 200, 255)    # 노랑: 구역 테두리 (마지막 촬영에서 찾은 위치)
COLOR_STATUS_BACKGROUND = (0, 0, 0)
COLOR_STATUS_TEXT = (255, 255, 255)
COLOR_VIOLATION_TEXT = (0, 0, 255)

# 자동 촬영 상태 → 화면 글자
STATE_LABELS = {STATE_MOVING: "MOVING", STATE_STILL: "STILL", STATE_WAITING: "CAPTURED - waiting for next scene"}


# 차량 박스를 그리는 것을 담당함.
def draw_vehicles(canvas, vehicles):
    for vehicle in vehicles:
        x1, y1, x2, y2 = vehicle["box"]
        # 소방차는 파랑, 나머지는 초록
        if vehicle.get("is_fire_truck"):
            box_color, label = COLOR_FIRE_TRUCK, "FIRE TRUCK"
        else:
            box_color, label = COLOR_VEHICLE, vehicle["vehicle_type"]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), box_color, 2)
        cv2.putText(canvas, label, (x1, max(y1 - 6, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)


# 마지막 촬영에서 찾은 구역 테두리를 그리는 것을 담당함.
def draw_zone(canvas, zone_polygon, zone_no):
    if not zone_polygon:
        return
    points = np.array(zone_polygon, dtype=np.int32)
    cv2.polylines(canvas, [points], True, COLOR_ZONE_LINE, 2)
    cv2.putText(canvas, zone_no or "", tuple(points[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_ZONE_LINE, 2)


# 왼쪽 위에 자동 촬영 상태와 마지막 결과를 쓰는 것을 담당함.
def draw_status(canvas, capture_state, still_seconds, last_result_line, has_violation):
    state_text = STATE_LABELS.get(capture_state, capture_state)
    # 멈춤 확인 중이면 몇 초째 멈춰 있는지 표시
    if capture_state == STATE_STILL:
        state_text = f"STILL {still_seconds:.1f}s"
    lines = [(f"AUTO CAPTURE: {state_text}", COLOR_STATUS_TEXT)]
    if last_result_line:
        lines.append((last_result_line, COLOR_VIOLATION_TEXT if has_violation else COLOR_STATUS_TEXT))

    # 검은 띠 위에 흰 글자 (어느 배경에서도 보이게)
    for line_index, (text, text_color) in enumerate(lines):
        y = 24 + line_index * 26
        (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(canvas, (6, y - 19), (14 + text_width, y + 7), COLOR_STATUS_BACKGROUND, -1)
        cv2.putText(canvas, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)


# 실시간 화면 한 장을 만드는 것을 담당함.
def draw_live_overlay(frame, vehicles, zone_polygon, zone_no, capture_state, still_seconds,
                      last_result_line, has_violation):
    """원본 프레임은 그대로 두고, 그린 복사본을 돌려준다."""
    canvas = frame.copy()
    draw_zone(canvas, zone_polygon, zone_no)
    draw_vehicles(canvas, vehicles)
    draw_status(canvas, capture_state, still_seconds, last_result_line, has_violation)
    return canvas
