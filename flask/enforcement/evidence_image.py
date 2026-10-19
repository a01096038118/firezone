"""단속 사진 만들기: 1차·2차 촬영 사진을 나란히 붙이고 촬영 시각·차량 박스·차량번호를 표시한다.

┌──────── 1차 촬영 ────────┬──────── 2차 촬영 ────────┐
│ 2026-10-19 10:00:00      │ 2026-10-19 10:00:15      │
│  [박스 12가3456]          │  [박스 12가3456]          │
└──────────────────────────┴──────────────────────────┘
OpenCV는 한글을 못 그려서 글자는 Pillow 로 그린다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from utils.time_format import format_readable_datetime

# 한 장의 높이 (두 사진을 같은 높이로 맞춤)
PANEL_HEIGHT = 720
HEADER_HEIGHT = 56
# 한글 글꼴 후보 (Windows 맑은 고딕 → 없으면 기본 글꼴)
KOREAN_FONT_PATHS = ("C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf",
                     "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
BOX_COLOR_BGR = (0, 0, 255)          # 빨강: 단속 차량 박스
ZONE_COLOR_BGR = (0, 200, 255)       # 노랑: 구역 테두리


# 한글 글꼴을 불러오는 것을 담당함.
def _load_font(size):
    for font_path in KOREAN_FONT_PATHS:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    # 한글 글꼴이 없으면 기본 글꼴 (한글이 깨질 수 있음)
    return ImageFont.load_default()


# 사진 한 장에 구역 테두리와 차량 박스를 그리고 높이를 맞추는 것을 담당함.
def _make_panel(shot, car):
    panel = shot.image.copy()
    # 구역 테두리
    if shot.zone_polygon_in_photo:
        cv2.polylines(panel, [np.array(shot.zone_polygon_in_photo, dtype=np.int32)], True, ZONE_COLOR_BGR, 3)
    # 단속 차량 박스
    x1, y1, x2, y2 = car.box
    cv2.rectangle(panel, (x1, y1), (x2, y2), BOX_COLOR_BGR, 4)
    # 두 사진 높이를 같게 맞춤
    scale = PANEL_HEIGHT / panel.shape[0]
    return cv2.resize(panel, (int(panel.shape[1] * scale), PANEL_HEIGHT)), scale


# 1차·2차 사진을 붙여 단속 사진 한 장을 만드는 것을 담당함.
def build_evidence_image(first_sighting, second_shot, second_car):
    """반환: BGR 이미지 (cv2.imwrite 로 저장 가능)"""
    first_panel, first_scale = _make_panel(first_sighting.shot, first_sighting.car)
    second_panel, second_scale = _make_panel(second_shot, second_car)

    # 위쪽에 글자 띠를 두고 두 사진을 가로로 붙임
    total_width = first_panel.shape[1] + second_panel.shape[1]
    canvas = np.full((HEADER_HEIGHT + PANEL_HEIGHT, total_width, 3), 255, dtype=np.uint8)
    canvas[HEADER_HEIGHT:, :first_panel.shape[1]] = first_panel
    canvas[HEADER_HEIGHT:, first_panel.shape[1]:] = second_panel

    # 한글 글자는 Pillow 로 그림
    pil_canvas = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_canvas)
    header_font, plate_font = _load_font(26), _load_font(30)
    panels = (
        (0, "1차 촬영", first_sighting.shot, first_sighting.car, first_scale),
        (first_panel.shape[1], "2차 촬영", second_shot, second_car, second_scale),
    )
    for panel_left, title, shot, car, scale in panels:
        # 위쪽 띠: "1차 촬영  2026-10-19 10:00:00"
        draw.text((panel_left + 16, 12), f"{title}  {format_readable_datetime(shot.captured_at)}",
                  font=header_font, fill=(0, 0, 0))
        # 차량 박스 위: 차량번호 (빨간 바탕에 흰 글자)
        label_x, label_y = int(car.box[0] * scale) + panel_left, int(car.box[1] * scale) + HEADER_HEIGHT - 40
        label_y = max(label_y, HEADER_HEIGHT)
        text_box = draw.textbbox((label_x, label_y), car.car_number, font=plate_font)
        draw.rectangle((text_box[0] - 6, text_box[1] - 4, text_box[2] + 6, text_box[3] + 4), fill=(220, 0, 0))
        draw.text((label_x, label_y), car.car_number, font=plate_font, fill=(255, 255, 255))
    # 두 사진 사이 구분선
    draw.line((first_panel.shape[1], 0, first_panel.shape[1], canvas.shape[0]), fill=(0, 0, 0), width=3)
    return cv2.cvtColor(np.array(pil_canvas), cv2.COLOR_RGB2BGR)
