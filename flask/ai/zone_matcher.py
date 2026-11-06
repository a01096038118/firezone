"""구역 자동 찾기·맞추기.

드론(카메라)이 같은 곳에 다시 와도 높이·각도가 조금씩 달라서 사진마다 구역 위치가 다르다.
구역마다 기준 사진 1장을 등록해두고, 새 사진이 오면 주차선·건물 같은 특징점을 서로 짝지어
① 어느 구역 사진인지 고르고 ② 사진이 기준 사진에서 얼마나 밀리고 돌았는지(homography) 계산한다.

맞추기에 실패하면 카메라에 정해둔 기본 구역(default_zone)이 있을 때만 "고정 좌표"로 처리한다.
"""
import logging
import os
import threading

import cv2
import numpy as np

import config

log = logging.getLogger(__name__)

MATCH_METHOD_FEATURE = "자동 맞추기"
MATCH_METHOD_FIXED = "고정 좌표"

_orb_detector = cv2.ORB_create(nfeatures=3000)
_matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
# 구역번호 → 기준 사진의 특징점 정보 (처음 쓸 때 계산해서 기억)
_reference_features_by_zone = {}
# 자동 촬영과 사진 올리기가 동시에 맞추기를 하지 않도록 잠금
_matching_lock = threading.Lock()


# 사진을 비교용 크기로 줄이고 줄인 비율을 돌려주는 것을 담당함.
def _shrink_for_matching(image):
    scale = min(1.0, config.ZONE_MATCH_IMAGE_WIDTH / image.shape[1])
    small_image = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1.0 else image
    return cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY), scale


# 기준 사진의 특징점을 처음 한 번만 계산하는 것을 담당함.
def _get_reference_features(zone):
    zone_no = zone["zone_no"]
    if zone_no not in _reference_features_by_zone:
        # 기준 사진을 읽음
        reference_image = cv2.imread(os.path.join(config.PROJECT_DIR, zone["reference_image"]))
        if reference_image is None:
            log.error("구역 %s 기준 사진을 읽을 수 없음: %s", zone_no, zone["reference_image"])
            _reference_features_by_zone[zone_no] = None
        else:
            # 줄인 기준 사진에서 특징점과 특징 설명값을 구함
            gray_image, scale = _shrink_for_matching(reference_image)
            keypoints, descriptors = _orb_detector.detectAndCompute(gray_image, None)
            _reference_features_by_zone[zone_no] = (keypoints, descriptors, scale)
    return _reference_features_by_zone[zone_no]


# 사진과 기준 사진 한 장을 맞춰보고 변환과 맞은 특징점 개수를 구하는 것을 담당함.
def _match_with_reference(photo_features, reference_features):
    photo_keypoints, photo_descriptors, photo_scale = photo_features
    reference_keypoints, reference_descriptors, reference_scale = reference_features
    if photo_descriptors is None or reference_descriptors is None:
        return None, 0

    # 특징점마다 가장 비슷한 두 개를 찾고, 첫 번째가 확실히 더 비슷한 것만 남김 (비율 검사)
    candidate_pairs = _matcher.knnMatch(photo_descriptors, reference_descriptors, k=2)
    good_matches = [pair[0] for pair in candidate_pairs
                    if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance]
    if len(good_matches) < config.ZONE_MATCH_MIN_INLIERS:
        return None, 0

    # 짝지은 점들로 사진→기준 사진 변환을 계산 (틀린 짝은 RANSAC 으로 걸러냄)
    photo_points = np.float32([photo_keypoints[match.queryIdx].pt for match in good_matches])
    reference_points = np.float32([reference_keypoints[match.trainIdx].pt for match in good_matches])
    small_homography, inlier_mask = cv2.findHomography(photo_points, reference_points, cv2.RANSAC, 5.0)
    if small_homography is None:
        return None, 0
    inlier_count = int(inlier_mask.sum())

    # 줄인 사진 기준 변환을 원본 크기 기준 변환으로 바꿈: (기준 줄임)⁻¹ · 변환 · (사진 줄임)
    shrink_photo = np.diag([photo_scale, photo_scale, 1.0])
    enlarge_reference = np.diag([1 / reference_scale, 1 / reference_scale, 1.0])
    return enlarge_reference @ small_homography @ shrink_photo, inlier_count


# 사진 크기를 기준 사진 크기로 그대로 늘리는 변환(고정 좌표)을 만드는 것을 담당함.
def _fixed_coordinate_transform(photo, zone):
    reference_width, reference_height = zone["reference_size"]
    photo_height, photo_width = photo.shape[:2]
    return np.diag([reference_width / photo_width, reference_height / photo_height, 1.0])


# 사진이 어느 구역인지 찾고 기준 사진에 맞추는 변환을 구하는 것을 담당함.
def find_zone_in_photo(photo, zones, default_zone_no=None):
    """반환: {"zone": 구역, "photo_to_reference": 3x3 변환, "method": 맞춘 방법, "inliers": 맞은 점 개수}
    어느 구역과도 맞지 않고 기본 구역도 없으면 None (판정 불가: 구역 확인 불가)."""
    with _matching_lock:
        # 사진의 특징점을 한 번만 계산
        gray_photo, photo_scale = _shrink_for_matching(photo)
        photo_keypoints, photo_descriptors = _orb_detector.detectAndCompute(gray_photo, None)
        photo_features = (photo_keypoints, photo_descriptors, photo_scale)

        # 등록된 구역마다 맞춰보고 가장 많이 맞은 구역을 고름
        best_match = None
        for zone in zones:
            reference_features = _get_reference_features(zone)
            if reference_features is None:
                continue
            photo_to_reference, inlier_count = _match_with_reference(photo_features, reference_features)
            if photo_to_reference is None or inlier_count < config.ZONE_MATCH_MIN_INLIERS:
                continue
            if best_match is None or inlier_count > best_match["inliers"]:
                best_match = {"zone": zone, "photo_to_reference": photo_to_reference,
                              "method": MATCH_METHOD_FEATURE, "inliers": inlier_count}
    if best_match is not None:
        return best_match

    # 맞추기에 실패하면 카메라 기본 구역이 있을 때만 고정 좌표로 처리
    default_zone = next((zone for zone in zones if zone["zone_no"] == default_zone_no), None)
    if default_zone is not None:
        log.info("구역 자동 맞추기 실패 → 기본 구역 %s 고정 좌표 사용", default_zone_no)
        return {"zone": default_zone, "photo_to_reference": _fixed_coordinate_transform(photo, default_zone),
                "method": MATCH_METHOD_FIXED, "inliers": 0}
    return None


# 구역 기준 사진이 바뀌었을 때 기억해둔 특징점을 지우는 것을 담당함.
def clear_reference_cache():
    _reference_features_by_zone.clear()
