"""등록하지 않은 장소에서 소방차 전용구역을 바닥 표시로 직접 찾기.

소방차 전용구역은 바닥에 노란 테두리(직선 4개로 된 사각형)와 노란 글씨("소방차 전용")가 칠해져 있다.
사진에서 노란 선을 골라내고, 노란 직선 4개로 둘러싸인 사각형 중 가장 구역다운 것을 구역 테두리로 쓴다.
네 꼭짓점을 정사각형(구역 좌표)으로 펴는 변환을 만들어, 1차·2차 사진의 차 위치를 같은 기준에서 비교한다.

등록된 구역 사진과 맞지 않을 때만 쓴다 (등록된 구역이 더 정확함).
- 노란색은 밝기 대신 "주변 바닥보다 얼마나 더 노란지"로 찾아서 그림자 속 선도 잡는다.
- 나무·풀(초록빛이 많은 곳) 근처의 노란빛은 바닥 칠로 보지 않는다.
- 구역 안 "소방차전용" 글씨는 테두리 직선을 찾을 때 뺀다.
- 구역이 화면 밖으로 잘려 한 변이 안 보이면 화면 가장자리를 그 변으로 쓴다.
- 윗변이 흐리거나 차에 가려 안 보이면, 두 옆변의 칠이 끝나는 점을 이어 윗변으로 쓴다.
- 테두리가 충분히 보이지 않으면 찾지 않는다(판정 불가). 엉뚱한 곳을 구역으로 잡아 단속하는 것보다 안전하다.
"""
import itertools
import logging

import cv2
import numpy as np

import config

log = logging.getLogger(__name__)

MATCH_METHOD_AUTO_MARKING = "바닥 표시 자동 인식"

# 구역 좌표(정사각형)의 한 변 길이. 네 꼭짓점을 이 크기 정사각형으로 편다
_ZONE_SQUARE_SIZE = 1000
# 구역을 찾을 때 줄이는 사진 가로 크기 (속도용. 4K 사진도 0.3초 안팎)
_WORK_WIDTH = 1280
# 테두리 후보로 쓸 노란 직선 개수 (긴 것부터)
_MAX_LINES = 12
# 화면 밖으로 잘린 구역은 이 비율까지 작아도 인정 (네 변이 다 보이는 구역은 AUTO_ZONE_MIN_AREA_RATIO)
_CUT_ZONE_MIN_AREA_RATIO = 0.02
# 화면 가장자리를 한 변으로 쓴 구역은 점수를 조금 낮춤 (네 변이 다 보이는 구역을 우선)
_CUT_ZONE_SCORE_FACTOR = 0.8


# 사진에서 노란 바닥 선(테두리·글씨)만 골라내는 것을 담당함.
def _yellow_line_mask(photo, vehicle_boxes):
    _, lab_a, lab_b = cv2.split(cv2.cvtColor(photo, cv2.COLOR_BGR2LAB))
    # 1. 주변 바닥보다 노란 정도(LAB b*)가 튀는 얇은 부분 (밝기와 상관없어서 그림자 속 선도 잡힘)
    kernel_size = max(15, int(photo.shape[1] * 0.03)) | 1
    yellow_tophat = cv2.morphologyEx(lab_b, cv2.MORPH_TOPHAT,
                                     cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size)))
    yellow = (yellow_tophat >= 8) & (lab_b >= 134) & (lab_a >= 118) & (lab_a <= 145)
    # 2. 나무·풀(초록빛이 많은 곳) 근처의 노란빛은 바닥 칠이 아니므로 지움
    green = ((lab_a < 120) & (lab_b > 128)).astype(np.float32)
    yellow &= cv2.blur(green, (kernel_size * 2, kernel_size * 2)) < 0.1
    mask = yellow.astype(np.uint8) * 255
    # 3. 차량 위의 노란색(택시 등)은 바닥 칠이 아니므로 지움
    # 박스 가장자리에는 차 옆 바닥 선이 걸쳐 있어서 박스 가운데 부분만 지움
    for x1, y1, x2, y2 in vehicle_boxes:
        margin_x, margin_y = int((x2 - x1) * 0.2), int((y2 - y1) * 0.2)
        mask[max(y1 + margin_y, 0):max(y2 - margin_y, 0), max(x1 + margin_x, 0):max(x2 - margin_x, 0)] = 0
    return mask


# 노란 칠 중 길고 가는 선(테두리)만 남기고 글씨처럼 짧고 뭉툭한 덩어리를 빼는 것을 담당함.
def _keep_long_lines(mask):
    """구역 가운데 세로로 쓰인 "소방차전용" 글씨가 직선으로 잡혀 테두리로 쓰이는 것을 막는다."""
    image_width = mask.shape[1]
    line_mask = np.zeros_like(mask)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    for label in range(1, count):
        x, y, box_width, box_height, pixel_count = stats[label]
        if pixel_count < 20:
            continue
        # 덩어리를 감싸는 가장 작은 (기울어진) 사각형의 긴 변·짧은 변
        ys, xs = np.where(labels[y:y + box_height, x:x + box_width] == label)
        _, (rect_width, rect_height), _ = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
        long_side, short_side = max(rect_width, rect_height), max(min(rect_width, rect_height), 1)
        # 아주 길거나, 어느 정도 길면서 가늘면 선
        if long_side >= image_width * 0.15 or (long_side >= image_width * 0.05 and long_side / short_side >= 4):
            line_mask[labels == label] = 255
    return line_mask


# 짧은 선분들을 같은 방향·위치끼리 묶어 긴 직선으로 만드는 것을 담당함.
def _merge_segments(segments, image_width):
    """반환: 직선 목록 [{"point", "direction", "length", "is_border", "ends"}] (긴 것부터)
    ends: 이 직선을 이루는 선분들의 끝점 (칠이 실제로 그려진 범위를 알 때 사용)"""
    lines = []
    for x1, y1, x2, y2 in segments:
        direction = np.array([x2 - x1, y2 - y1], float)
        length = np.linalg.norm(direction)
        direction /= length
        # 방향을 한쪽으로 통일 (왼→오른쪽, 같으면 위→아래)
        if direction[0] < 0 or (direction[0] == 0 and direction[1] < 0):
            direction = -direction
        middle = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
        # 방향 차이 4도 이내, 거리 차이 가로의 1.2% 이내면 같은 직선
        for line in lines:
            normal = np.array([-line["direction"][1], line["direction"][0]])
            if abs(np.dot(line["direction"], direction)) > np.cos(np.radians(4)) \
                    and abs(np.dot(middle - line["point"], normal)) < image_width * 0.012:
                total_length = line["length"] + length
                line["point"] = (line["point"] * line["length"] + middle * length) / total_length
                line["length"] = total_length
                line["ends"] += [(x1, y1), (x2, y2)]
                break
        else:
            lines.append({"point": middle, "direction": direction, "length": length, "is_border": False,
                          "ends": [(x1, y1), (x2, y2)]})
    return sorted(lines, key=lambda line: -line["length"])


# 두 옆변의 칠이 끝나는 점을 이어 안 보이는 변(흐리거나 가려진 윗변)을 만드는 것을 담당함.
def _closing_line(side_a, side_b, opposite):
    """opposite(보이는 아랫변)에서 먼 쪽 끝점끼리 잇는다. 칠이 없어도 되는 변으로 표시 (is_border=True)."""
    far_ends = []
    for side in (side_a, side_b):
        ends = np.array(side["ends"], float)
        # opposite 직선에서 가장 먼 끝점
        normal = np.array([-opposite["direction"][1], opposite["direction"][0]])
        far_ends.append(ends[np.argmax(np.abs((ends - opposite["point"]) @ normal))])
    direction = far_ends[1] - far_ends[0]
    length = np.linalg.norm(direction)
    if length == 0:
        return None
    return {"point": far_ends[0], "direction": direction / length, "length": 0, "is_border": True, "ends": []}


# 화면 가장자리(아래·왼쪽·오른쪽)를 직선으로 만드는 것을 담당함 (화면 밖으로 잘린 구역용).
def _border_lines(width, height):
    edges = (((0, height - 1), (1, 0)), ((0, 0), (0, 1)), ((width - 1, 0), (0, 1)))
    return [{"point": np.array(point, float), "direction": np.array(direction, float), "length": 0, "is_border": True,
             "ends": []} for point, direction in edges]


# 두 직선이 만나는 점을 구하는 것을 담당함.
def _intersect(line_a, line_b):
    """평행하면 None."""
    matrix = np.array([line_a["direction"], -line_b["direction"]]).T
    if abs(np.linalg.det(matrix)) < 1e-6:
        return None
    t = np.linalg.solve(matrix, line_b["point"] - line_a["point"])
    return line_a["point"] + t[0] * line_a["direction"]


# 사각형의 한 변을 따라 노란 칠이 얼마나 있는지(0~1) 계산하는 것을 담당함.
def _edge_coverage(near_paint, start, end):
    height, width = near_paint.shape
    sample_count = max(int(np.linalg.norm(end - start) / 3), 10)
    xs = np.linspace(start[0], end[0], sample_count).astype(int)
    ys = np.linspace(start[1], end[1], sample_count).astype(int)
    inside = (xs >= 0) & (xs < width) & (ys >= 0) & (ys < height)
    # 변의 절반 이상이 화면 밖이면 확인할 수 없음
    if inside.sum() < sample_count * 0.5:
        return 0.0
    return near_paint[ys[inside], xs[inside]].mean() / 255


# 직선 4개로 만든 사각형이 소방구역 테두리다운지 점수를 매기는 것을 담당함.
def _score_quad(quad, edge_lines, mask, near_paint):
    """반환: 점수 (구역이 아니면 None)"""
    height, width = mask.shape
    photo_area = width * height

    # 1. 화면에서 크게 벗어난 꼭짓점, 꼬인 모양(X자), 너무 작거나 큰 모양 제외
    if np.any(quad < -0.15 * width) or np.any(quad[:, 0] > 1.15 * width) or np.any(quad[:, 1] > height + 0.15 * width):
        return None
    hull = cv2.convexHull(quad)
    area = cv2.contourArea(quad)
    if len(hull) != 4 or area < cv2.contourArea(hull) * 0.98:
        return None
    if area < photo_area * _CUT_ZONE_MIN_AREA_RATIO or area > photo_area * 0.8:
        return None
    # 납작한 모양 제외
    if min(np.linalg.norm(quad[i] - quad[(i + 1) % 4]) for i in range(4)) < width * 0.05:
        return None
    # 세모처럼 뾰족한 모양 제외 (사각형 구역은 비스듬히 찍어도 꼭짓점 각도가 30~150도)
    for i in range(4):
        to_previous, to_next = quad[i - 1] - quad[i], quad[(i + 1) % 4] - quad[i]
        cos_angle = np.dot(to_previous, to_next) / (np.linalg.norm(to_previous) * np.linalg.norm(to_next))
        if not 30 <= np.degrees(np.arccos(np.clip(cos_angle, -1, 1))) <= 150:
            return None

    # 2. 변마다 노란 선이 그려져 있어야 함 (화면 가장자리 변은 제외)
    coverages = [_edge_coverage(near_paint, quad[i], quad[(i + 1) % 4])
                 for i in range(4) if not edge_lines[i]["is_border"]]
    coverages.sort()
    is_cut_zone = len(coverages) < 4
    if is_cut_zone:
        # 잘린 구역은 보이는 세 변이 모두 뚜렷해야 함
        if coverages[0] < 0.6 or np.mean(coverages) < 0.75:
            return None
    else:
        # 네 변이 다 보이는 구역은 차에 가려 한 변이 덜 보일 수 있음
        if area < photo_area * config.AUTO_ZONE_MIN_AREA_RATIO:
            return None
        if coverages[0] < 0.3 or coverages[1] < 0.5 or np.mean(coverages) < config.AUTO_ZONE_MIN_OUTLINE_COVERAGE:
            return None

    # 3. 안쪽이 노랗게 꽉 차 있으면(횡단보도·노란 벽) 제외. 구역 안은 글씨 정도만 칠해져 있음
    filled = np.zeros_like(mask)
    cv2.fillConvexPoly(filled, quad.astype(np.int32), 255)
    inner = cv2.erode(filled, np.ones((15, 15), np.uint8))
    if cv2.countNonZero(mask & inner) / max(cv2.countNonZero(inner), 1) > config.AUTO_ZONE_MAX_PAINT_RATIO:
        return None

    # 4. 실제 구역은 선이 꼭짓점에서 만남. 화면 안 꼭짓점 중 칠이 없는 것은 1개(차에 가림)까지만 허용
    corner_radius = int(width * 0.015)
    empty_corner_count = 0
    for x, y in quad.astype(int):
        if 0 <= x < width and 0 <= y < height:
            corner = near_paint[max(y - corner_radius, 0):y + corner_radius + 1,
                                max(x - corner_radius, 0):x + corner_radius + 1]
            if cv2.countNonZero(corner) == 0:
                empty_corner_count += 1
    if empty_corner_count > 1:
        return None

    # 테두리가 뚜렷하고 클수록 높은 점수
    score = np.mean(coverages) ** 2 * np.sqrt(area / photo_area)
    return score * _CUT_ZONE_SCORE_FACTOR if is_cut_zone else score


# 네 꼭짓점을 왼쪽 위, 오른쪽 위, 오른쪽 아래, 왼쪽 아래 순서로 정렬하는 것을 담당함.
def _order_corners(corners):
    by_height = corners[np.argsort(corners[:, 1])]
    top = by_height[:2][np.argsort(by_height[:2, 0])]
    bottom = by_height[2:][np.argsort(by_height[2:, 0])]
    return np.array([top[0], top[1], bottom[1], bottom[0]], dtype=np.float32)


# 노란 직선들 중 구역 테두리가 되는 4개를 고르는 것을 담당함.
def _find_zone_quad(mask):
    """반환: 네 꼭짓점 (작업 크기 기준) 또는 None"""
    height, width = mask.shape
    # 1. 글씨를 뺀 노란 선에서 직선 조각을 찾고 같은 직선끼리 묶음
    segments = cv2.HoughLinesP(_keep_long_lines(mask), 1, np.pi / 180, 30, minLineLength=int(width * 0.04), maxLineGap=int(width * 0.02))
    if segments is None:
        return None
    paint_lines = _merge_segments(segments[:, 0], width)[:_MAX_LINES]
    near_paint = cv2.dilate(mask, np.ones((7, 7), np.uint8))

    # 2. 사각형 후보: 직선 4개 (화면 가장자리는 한 변까지)
    #    + 옆변 2개와 아랫변 1개만 보일 때 옆변 끝을 이은 변 (윗변이 흐리거나 가려진 경우)
    # 직선 4개를 마주 보는 두 쌍으로 나누는 방법 (a·b 가 마주 보고 c·d 가 마주 봄)
    all_pairings = (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)))
    candidates = [(lines, all_pairings) for lines in itertools.combinations(paint_lines + _border_lines(width, height), 4)
                  if sum(line["is_border"] for line in lines) <= 1]
    for side_a, side_b in itertools.combinations(paint_lines, 2):
        for opposite in paint_lines:
            if opposite is side_a or opposite is side_b:
                continue
            closing = _closing_line(side_a, side_b, opposite)
            # 옆변끼리 마주 보고, 아랫변과 이은 변이 마주 봄
            if closing is not None:
                candidates.append(((side_a, side_b, opposite, closing), (((0, 1), (2, 3)),)))

    # 3. 가장 구역다운 사각형을 고름
    best_quad, best_score = None, 0.0
    for lines, pairings in candidates:
        for (a, b), (c, d) in pairings:
            corners = [_intersect(lines[a], lines[c]), _intersect(lines[c], lines[b]),
                       _intersect(lines[b], lines[d]), _intersect(lines[d], lines[a])]
            if any(corner is None for corner in corners):
                continue
            quad = np.array(corners, np.float32)
            # 꼭짓점 i → i+1 변이 어느 직선인지
            edge_lines = [lines[c], lines[b], lines[d], lines[a]]
            score = _score_quad(quad, edge_lines, mask, near_paint)
            if score is not None and score > best_score:
                best_quad, best_score = quad, score
    return best_quad


# 등록되지 않은 사진에서 바닥 표시로 소방차 전용구역을 찾는 것을 담당함.
def find_zone_by_marking(photo, vehicle_boxes=()):
    """반환: zone_matcher.find_zone_in_photo 와 같은 모양 {"zone", "photo_to_reference", "method", "inliers"}
    바닥 표시를 찾지 못하면 None (판정 불가)."""
    photo_height, photo_width = photo.shape[:2]

    # 1. 속도를 위해 사진을 줄이고 노란 선을 골라냄
    scale = min(1.0, _WORK_WIDTH / photo_width)
    small_photo = cv2.resize(photo, None, fx=scale, fy=scale) if scale < 1 else photo
    small_boxes = [[int(value * scale) for value in box] for box in vehicle_boxes]
    mask = _yellow_line_mask(small_photo, small_boxes)

    # 2. 노란 직선 4개로 둘러싸인 구역 테두리를 찾음
    quad = _find_zone_quad(mask)
    if quad is None:
        return None
    corners = _order_corners(quad / scale)

    # 3. 네 꼭짓점을 정사각형으로 펴는 변환 (사진 → 구역 좌표)
    square = np.array([[0, 0], [_ZONE_SQUARE_SIZE, 0], [_ZONE_SQUARE_SIZE, _ZONE_SQUARE_SIZE],
                       [0, _ZONE_SQUARE_SIZE]], dtype=np.float32)
    photo_to_zone = cv2.getPerspectiveTransform(corners, square)
    log.info("바닥 표시로 구역 인식: 사진의 %.1f%% 크기, 꼭짓점 %s",
             cv2.contourArea(corners) / (photo_width * photo_height) * 100, corners.astype(int).tolist())

    zone = {
        "zone_no": config.AUTO_ZONE_NO,
        "name": "자동 인식 구역",
        "violation_type": config.DEFAULT_VIOLATION_TYPE,
        "reference_image": None,
        "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        "reference_size": (_ZONE_SQUARE_SIZE, _ZONE_SQUARE_SIZE),
    }
    return {"zone": zone, "photo_to_reference": photo_to_zone, "method": MATCH_METHOD_AUTO_MARKING, "inliers": 0}
