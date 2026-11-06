"""Flask AI 서버 시작점."""
from flask import Flask

import config
from utils.logger import setup_logging


# Flask 앱을 만들고 API 를 등록하는 것을 담당함.
def create_app():
    # 로그 설정은 여기서 한 번만 (OCR 별도 프로세스가 이 파일을 다시 읽어도 중복되지 않게)
    setup_logging()

    from camera.monitoring import monitoring
    from routes.health import health_bp
    from routes.images import images_bp
    from routes.monitor import monitor_bp
    from routes.photos import photos_bp
    from routes.results import results_bp

    app = Flask(__name__)
    app.json.ensure_ascii = False   # JSON 응답의 한글을 그대로 보여줌

    # API 등록 (/api/...)
    for api_blueprint in (monitor_bp, photos_bp, images_bp, results_bp, health_bp):
        app.register_blueprint(api_blueprint, url_prefix="/api")

    # Boot 화면(다른 주소)에서 영상·사진·API 를 불러갈 수 있게 허용(CORS)하는 것을 담당함.
    @app.after_request
    def allow_cross_origin(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    # 실시간 관제 시작
    if config.START_MONITORING_ON_BOOT:
        monitoring()
    return app


if __name__ == "__main__":
    create_app().run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False, threaded=True)
