"""저장된 사진 제공 API. Boot 화면이 dl_image_path 주소로 단속 사진을 불러갈 때 쓴다."""
from flask import Blueprint, abort, send_from_directory

import config

images_bp = Blueprint("images", __name__)

# 주소 앞부분 → 실제 폴더
IMAGE_FOLDERS = {
    "detections": config.DETECTION_IMAGE_DIR,   # 단속 사진 (1차+2차)
    "photos": config.PHOTO_DIR,                 # 촬영 원본
}


# 단속 사진·촬영 원본 제공 API(GET /api/images/<종류>/<경로>)를 담당함.
@images_bp.route("/images/<folder>/<path:image_path>", methods=["GET"])
def get_image(folder, image_path):
    # 정해진 폴더만 허용 (다른 폴더 접근 차단)
    if folder not in IMAGE_FOLDERS:
        abort(404)
    # send_from_directory 가 폴더 밖 경로(../)를 막아줌
    return send_from_directory(IMAGE_FOLDERS[folder], image_path)
