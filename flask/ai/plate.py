"""번호판 인식 (MON-005).

OCR은 CPU를 많이 써서 실시간 화면을 멈추게 하므로, ai/plate_reader.py 가 별도 프로세스에서 실행한다.
"""
import os
import re
import threading

import cv2
import numpy as np
from ultralytics import YOLO

import config

# 한국 번호판 형식: 12가3456, 123가4567 (두 줄 번호판 "서울12 / 가3456" 은 이어 붙이면 12가3456)
KOREAN_PLATE_PATTERN = re.compile(r"\d{2,3}[가-힣]\d{4}")

# OCR에 넣기 전 이미지 가로 크기 범위 (너무 크면 느리고, 너무 작으면 글자가 뭉개짐)
OCR_MAX_IMAGE_WIDTH = 960
OCR_MIN_IMAGE_WIDTH = 480

_plate_detect_model = None
_ocr_engine = None
# OCR 엔진은 여러 스레드가 동시에 쓰면 안 되므로 잠금
_ocr_lock = threading.Lock()


# 번호판 위치 탐지 모델을 처음 한 번만 불러오는 것을 담당함.
def _get_plate_detect_model():
    """번호판 위치를 찾는 전용 모델. 모델 파일이 없으면 None."""
    global _plate_detect_model
    if _plate_detect_model is None and os.path.exists(config.PLATE_MODEL_PATH):
        _plate_detect_model = YOLO(config.PLATE_MODEL_PATH)
    return _plate_detect_model


# 글자 인식(OCR) 엔진을 처음 한 번만 불러오는 것을 담당함.
def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(
            # 기본값(server)은 CPU에서 10초 이상 걸려서 가벼운 mobile 모델 사용
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="korean_PP-OCRv5_mobile_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,                # Windows CPU 에서 oneDNN 오류 회피
            cpu_threads=config.OCR_CPU_THREADS,  # 실시간 화면이 쓸 CPU를 남겨둠
        )
    return _ocr_engine


# OCR에 알맞은 크기로 이미지를 줄이거나 키우는 것을 담당함.
def _resize_for_ocr(image):
    image_height, image_width = image.shape[:2]
    # 너무 크면 줄임 (속도)
    if image_width > OCR_MAX_IMAGE_WIDTH:
        scale = OCR_MAX_IMAGE_WIDTH / image_width
    # 너무 작으면 키움 (작은 번호판 글자가 뭉개지지 않게)
    elif image_width < OCR_MIN_IMAGE_WIDTH:
        scale = OCR_MIN_IMAGE_WIDTH / image_width
    else:
        return image
    return cv2.resize(image, (int(image_width * scale), int(image_height * scale)), interpolation=cv2.INTER_CUBIC)


# 차량 이미지에서 번호판 부분만 잘라내는 것을 담당함.
def _crop_plate_area(vehicle_image):
    """번호판 모델이 없으면 차량 이미지 전체를 그대로 쓴다. 번호판을 못 찾으면 None."""
    plate_model = _get_plate_detect_model()
    if plate_model is None:
        return vehicle_image

    # 번호판 모델로 가장 확실한 번호판 하나를 고름
    plate_boxes = plate_model.predict(vehicle_image, conf=config.PLATE_MIN_CONFIDENCE, verbose=False)[0].boxes
    if plate_boxes is None or len(plate_boxes) == 0:
        return None
    most_confident = int(plate_boxes.conf.argmax())
    x1, y1, x2, y2 = (int(coord) for coord in plate_boxes.xyxy[most_confident].tolist())
    return vehicle_image[y1:y2, x1:x2]


# 차량 이미지에서 차량번호를 읽어내는 것을 담당함.
def recognizeLicensePlate(vehicle_image):
    """차량 이미지에서 번호판을 읽어 차량번호(예: "12가3456")를 반환한다. 못 읽으면 None.
    오류가 나면 예외를 그대로 올려서, 호출한 쪽이 로그를 남기게 한다."""
    if vehicle_image is None or vehicle_image.size == 0:
        return None

    with _ocr_lock:
        # 번호판 부분을 잘라냄
        plate_image = _crop_plate_area(vehicle_image)
        if plate_image is None or plate_image.size == 0:
            return None
        # 글자 인식
        ocr_results = _get_ocr_engine().predict(_resize_for_ocr(plate_image))

    # 읽은 글자를 모두 이어 붙이고 공백을 지움 (두 줄 번호판도 한 줄이 됨)
    recognized_texts = []
    for ocr_result in ocr_results:
        recognized_texts.extend(ocr_result["rec_texts"])
    all_text_without_spaces = re.sub(r"\s+", "", "".join(recognized_texts))

    # 한국 번호판 형식에 맞는 부분만 꺼냄
    plate_match = KOREAN_PLATE_PATTERN.search(all_text_without_spaces)
    return plate_match.group() if plate_match else None


# 번호판 인식 모델과 OCR 엔진을 미리 불러오고 한 번 돌려보는 것(워밍업)을 담당함.
def warmup_plate_reader():
    """첫 번호판 인식이 OCR 로딩 때문에 늦어지는 것을 막는다."""
    blank_image = np.full((64, 200, 3), 255, dtype=np.uint8)
    with _ocr_lock:
        # 번호판 모델이 있으면 같이 불러옴
        if _get_plate_detect_model() is not None:
            _get_plate_detect_model().predict(blank_image, verbose=False)
        _get_ocr_engine().predict(blank_image)
