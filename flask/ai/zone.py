"""구역 좌표 계산.

구역 테두리는 기준 사진 위의 비율 좌표(0~1)로 저장한다.
사진을 기준 사진에 맞춘 변환(homography)으로, 사진 속 위치를 기준 사진 위치로 바꿔서 비교한다.
"""
import cv2
import numpy as np


# 차량 박스에서 바퀴가 땅에 닿는 지점을 구하는 것을 담당함.
def get_ground_point(box):
    """박스 아래쪽 가운데. 차량이 구역 안인지 판단할 때 쓴다."""
    x1, _, x2, y2 = box
    return ((x1 + x2) / 2, y2)


# 사진 속 점들을 기준 사진 좌표로 바꾸는 것을 담당함.
def photo_points_to_reference(points, photo_to_reference):
    # OpenCV 변환 함수가 받는 모양 (점 개수, 1, 2) 으로 바꿔서 변환
    point_array = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(point_array, photo_to_reference).reshape(-1, 2).tolist()


# 차량 박스를 기준 사진 좌표의 박스로 바꾸는 것을 담당함.
def box_to_reference(box, photo_to_reference):
    """박스 네 꼭짓점을 바꾼 뒤, 그 점들을 감싸는 박스를 돌려준다."""
    x1, y1, x2, y2 = box
    corners = photo_points_to_reference([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], photo_to_reference)
    xs, ys = [corner[0] for corner in corners], [corner[1] for corner in corners]
    return (min(xs), min(ys), max(xs), max(ys))


# 차량이 바닥에 닿는 부분을 구역 좌표의 박스로 바꾸는 것을 담당함 (바닥 표시로 찾은 구역용).
def ground_box_to_reference(box, photo_to_reference):
    """구역을 정사각형으로 크게 펴면 차의 윗부분(지붕)은 지나치게 늘어나므로
    바퀴 쪽 아래 모서리 두 점만 바꾸고, 그 폭의 절반 높이를 차가 차지한 바닥으로 본다."""
    x1, _, x2, y2 = box
    (left_x, left_y), (right_x, right_y) = photo_points_to_reference([(x1, y2), (x2, y2)], photo_to_reference)
    ground_y = (left_y + right_y) / 2
    footprint_height = abs(right_x - left_x) / 2
    return (min(left_x, right_x), ground_y - footprint_height, max(left_x, right_x), ground_y)


# 구역 테두리(비율 좌표)를 기준 사진의 픽셀 좌표로 바꾸는 것을 담당함.
def zone_polygon_in_reference(zone):
    reference_width, reference_height = zone["reference_size"]
    return [(ratio_x * reference_width, ratio_y * reference_height) for ratio_x, ratio_y in zone["polygon"]]


# 구역 테두리를 사진 위의 픽셀 좌표로 바꾸는 것을 담당함 (화면에 그릴 때 사용).
def zone_polygon_in_photo(zone, photo_to_reference):
    # 사진→기준 변환을 거꾸로 돌려 기준→사진으로 바꿈
    reference_to_photo = np.linalg.inv(photo_to_reference)
    return [tuple(int(value) for value in point)
            for point in photo_points_to_reference(zone_polygon_in_reference(zone), reference_to_photo)]


# 사진 속 점이 사진 위에 그린 구역 테두리 안에 있는지 확인하는 것을 담당함.
def is_point_in_photo_polygon(photo_point, polygon_in_photo):
    polygon = np.array(polygon_in_photo, dtype=np.float32)
    # 0 이상이면 안쪽 또는 테두리 위
    return cv2.pointPolygonTest(polygon, (float(photo_point[0]), float(photo_point[1])), False) >= 0


# 두 박스가 얼마나 겹치는지(0~1) 계산하는 것을 담당함.
def box_overlap_ratio(first_box, second_box):
    """겹친 넓이 / 두 박스를 합친 넓이 (IoU). 1이면 완전히 같은 자리."""
    # 겹치는 부분의 왼쪽 위·오른쪽 아래
    left, top = max(first_box[0], second_box[0]), max(first_box[1], second_box[1])
    right, bottom = min(first_box[2], second_box[2]), min(first_box[3], second_box[3])
    overlap_area = max(0, right - left) * max(0, bottom - top)
    # 두 박스 넓이의 합에서 겹친 부분을 한 번 뺌
    first_area = (first_box[2] - first_box[0]) * (first_box[3] - first_box[1])
    second_area = (second_box[2] - second_box[0]) * (second_box[3] - second_box[1])
    union_area = first_area + second_area - overlap_area
    return overlap_area / union_area if union_area > 0 else 0.0
