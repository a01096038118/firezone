"""등록하지 않은 장소에서 소방차 전용구역을 바닥 표시로 직접 찾기.

소방차 전용구역은 바닥에 노란 테두리·노란 글씨("소방차 전용")와 빨간 빗금이 칠해져 있다.
사진에서 노란색·빨간색 칠을 찾아 가장 큰 덩어리를 감싸는 네 꼭짓점을 구역 테두리로 쓴다.
네 꼭짓점을 정사각형(구역 좌표)으로 펴는 변환을 만들어, 1차·2차 사진의 차 위치를 같은 기준에서 비교한다.

등록된 구역 사진과 맞지 않을 때만 쓴다 (등록된 구역이 더 정확함).
테두리가 차에 가려 일부 안 보이면 보이는 칠까지만 구역으로 잡는다.
그래서 구역이 실제보다 작게 잡힐 수는 있어도(단속 놓침) 구역 밖 차를 단속하지는 않는다.
"""
import logging

import cv2
import numpy as np

import config

log = logging.getLogger(__name__)

MATCH_METHOD_AUTO_MARKING = "바닥 표시 자동 인식"

# 구역 좌표(정사각형)의 한 변 길이. 네 꼭짓점을 이 크기 정사각형으로 편다
_ZONE_SQUARE_SIZE = 1000


# 사진에서 노란색·빨간색 바닥 칠만 골라내는 것을 담당함.
def _paint_mask(photo, vehicle_boxes):
    hsv = cv2.cvtColor(photo, cv2.COLOR_BGR2HSV)
    # 노란 테두리·글씨
    yellow = cv2.inRange(hsv, (15, 80, 100), (40, 255, 255))
    # 빨간 빗금 (빨간색은 색상값 양 끝에 걸쳐 있어서 두 구간)
    red = cv2.inRange(hsv, (0, 90, 70), (10, 255, 255)) | cv2.inRange(hsv, (165, 90, 70), (180, 255, 255))
    mask = yellow | red
    # 차량 위의 노란색·빨간색(택시, 빨간 차)은 바닥 칠이 아니므로 지움
    # 박스 가장자리에는 차 옆 바닥 선이 걸쳐 있어서 박스 가운데 부분만 지움
    for x1, y1, x2, y2 in vehicle_boxes:
        margin_x, margin_y = int((x2 - x1) * 0.2), int((y2 - y1) * 0.2)
        mask[max(y1 + margin_y, 0):max(y2 - margin_y, 0), max(x1 + margin_x, 0):max(x2 - margin_x, 0)] = 0
    return mask


# 덩어리를 감싸는 테두리를 네 꼭짓점으로 줄이는 것을 담당함.
def _four_corners(hull):
    """반환: 네 꼭짓점 (왼쪽 위, 오른쪽 위, 오른쪽 아래, 왼쪽 아래 순서)"""
    points = hull.reshape(-1, 2).astype(np.float32)
    # 후보 1: 가장 바깥쪽 네 점 (왼위 = x+y 최소, 오위 = x-y 최대, 오아래 = x+y 최대, 왼아래 = x-y 최소)
    sums, diffs = points.sum(axis=1), points[:, 0] - points[:, 1]
    candidates = [np.array([points[sums.argmin()], points[diffs.argmax()],
                            points[sums.argmax()], points[diffs.argmin()]], dtype=np.float32)]
    # 후보 2: 테두리를 점점 크게 단순화해서 꼭짓점이 4개가 된 모양들 (사진이 많이 돌아갔을 때 유리)
    perimeter = cv2.arcLength(hull, True)
    for ratio in np.arange(0.01, 0.1, 0.005):
        approx = cv2.approxPolyDP(hull, ratio * perimeter, True)
        if len(approx) == 4:
            candidates.append(approx.reshape(4, 2).astype(np.float32))
    # 덩어리를 가장 많이 덮는(넓이가 가장 큰) 네 꼭짓점을 고름
    corners = max(candidates, key=lambda quad: cv2.contourArea(quad))

    # 위쪽 두 점과 아래쪽 두 점으로 나눈 뒤 각각 왼쪽→오른쪽으로 정렬
    by_height = corners[np.argsort(corners[:, 1])]
    top = by_height[:2][np.argsort(by_height[:2, 0])]
    bottom = by_height[2:][np.argsort(by_height[2:, 0])]
    return np.array([top[0], top[1], bottom[1], bottom[0]], dtype=np.float32)


# 덩어리 테두리를 따라 실제로 칠이 얼마나 있는지(0~1) 계산하는 것을 담당함.
def _outline_coverage(mask, hull, band_width):
    """구역 표시는 테두리 선이 그려져 있어서 높고, 나무·잡동사니처럼 흩어진 색은 낮다."""
    # 덩어리 테두리를 따라 band_width 두께의 띠를 만들고, 띠 위의 점 중 칠이 있는 비율
    band = np.zeros(mask.shape, np.uint8)
    cv2.polylines(band, [hull], True, 255, band_width)
    near_paint = cv2.dilate(mask, np.ones((band_width, band_width), np.uint8))
    band_pixels = cv2.countNonZero(band)
    return cv2.countNonZero(band & near_paint) / band_pixels if band_pixels else 0.0


# 등록되지 않은 사진에서 바닥 표시로 소방차 전용구역을 찾는 것을 담당함.
def find_zone_by_marking(photo, vehicle_boxes=()):
    """반환: zone_matcher.find_zone_in_photo 와 같은 모양 {"zone", "photo_to_reference", "method", "inliers"}
    바닥 표시를 찾지 못하면 None (판정 불가)."""
    photo_height, photo_width = photo.shape[:2]
    photo_area = photo_height * photo_width

    # 1. 노란색·빨간색 칠을 골라내고, 떨어진 선·글씨가 한 덩어리가 되도록 이어 붙임
    mask = _paint_mask(photo, vehicle_boxes)
    kernel_size = max(3, int(photo_width * 0.015))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((kernel_size, kernel_size), np.uint8))

    # 2. 덩어리마다 감싸는 테두리를 구하고, 구역다운 것 중 가장 큰 것을 고름
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_hull, best_area = None, 0.0
    for contour in contours:
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        # 너무 작은 덩어리(차선 조각, 표지판)는 제외
        if hull_area < photo_area * config.AUTO_ZONE_MIN_AREA_RATIO:
            continue
        # 꽉 찬 색 덩어리(노란 벽, 간판)는 제외. 구역 표시는 테두리·빗금·글씨라 속이 비어 있음
        paint_ratio = cv2.countNonZero(mask & _fill(mask.shape, hull)) / hull_area
        if paint_ratio > config.AUTO_ZONE_MAX_PAINT_RATIO:
            continue
        # 테두리 선이 충분히 그려져 있어야 함 (흩어진 나무·간판 색 제외)
        if _outline_coverage(mask, hull, kernel_size) < config.AUTO_ZONE_MIN_OUTLINE_COVERAGE:
            continue
        if hull_area > best_area:
            best_hull, best_area = hull, hull_area
    if best_hull is None:
        return None

    # 3. 네 꼭짓점을 정사각형으로 펴는 변환 (사진 → 구역 좌표)
    corners = _four_corners(best_hull)
    square = np.array([[0, 0], [_ZONE_SQUARE_SIZE, 0], [_ZONE_SQUARE_SIZE, _ZONE_SQUARE_SIZE],
                       [0, _ZONE_SQUARE_SIZE]], dtype=np.float32)
    photo_to_zone = cv2.getPerspectiveTransform(corners, square)
    log.info("바닥 표시로 구역 인식: 사진의 %.1f%% 크기, 꼭짓점 %s",
             best_area / photo_area * 100, corners.astype(int).tolist())

    zone = {
        "zone_no": config.AUTO_ZONE_NO,
        "name": "자동 인식 구역",
        "violation_type": config.DEFAULT_VIOLATION_TYPE,
        "reference_image": None,
        "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "reference_size": (_ZONE_SQUARE_SIZE, _ZONE_SQUARE_SIZE),
    }
    return {"zone": zone, "photo_to_reference": photo_to_zone, "method": MATCH_METHOD_AUTO_MARKING, "inliers": 0}


# 테두리 안쪽을 채운 그림을 만드는 것을 담당함 (칠 비율 계산용).
def _fill(shape, hull):
    filled = np.zeros(shape, np.uint8)
    cv2.fillConvexPoly(filled, hull, 255)
    return filled
