from ultralytics import YOLO
import cv2
from paddleocr import PaddleOCR
from ai.constants import NUMBER_PLATE

# YOLO 모델을 로딩함.
yolo_model = YOLO("yolov8n.pt")
ocr = PaddleOCR(lang='korean')

def recognize_plate(image_path):
    results = yolo_model(image_path)
    img = cv2.imread(image_path)
    plate_texts = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            if cls == NUMBER_PLATE:  # 번호판 클래스 상수 사용
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_img = img[y1:y2, x1:x2]

                # OCR 사용하여 번호판의 글자를 인식함.
                ocr_result = ocr.ocr(plate_img, det=True, rec=True)
                for line in ocr_result[0]:
                    plate_texts.append(line[1][0])

    return plate_texts[0] if plate_texts else "인식실패"
