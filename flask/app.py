from flask import Flask
from routes.detect import detect_bp

app = Flask(__name__)

# BP를 등록함.
app.register_blueprint(detect_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
