"""로그 설정: 콘솔 출력 + 날짜별 파일 저장.

logs/server_2026-10-19.log     서버 전체 로그
logs/violation_2026-10-19.log  위반 기록(고지서 형식) + 판정 불가 기록 (utils/violation_log.py 가 기록)

로그 파일은 자동으로 지우지 않는다. (기록 삭제는 관리자만 할 수 있음)
"""
import logging
import os
from datetime import date

import config

SERVER_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
VIOLATION_LOGGER_NAME = "violation"


# 날짜가 들어간 파일 이름으로 로그를 남기고, 날짜가 바뀌면 새 파일로 넘어가는 것을 담당함.
class DailyFileHandler(logging.FileHandler):
    # 오늘 날짜 로그 파일을 여는 것을 담당함.
    def __init__(self, file_prefix):
        self.file_prefix = file_prefix
        self.current_date = date.today()
        # 로그 폴더가 없으면 만듦
        os.makedirs(config.LOG_DIR, exist_ok=True)
        super().__init__(self._log_path_for(self.current_date), encoding="utf-8")

    # 날짜에 맞는 로그 파일 경로를 만드는 것을 담당함. 예: logs/server_2026-10-19.log
    def _log_path_for(self, log_date):
        return os.path.join(config.LOG_DIR, f"{self.file_prefix}_{log_date:%Y-%m-%d}.log")

    # 날짜가 바뀌었으면 새 파일로 바꾼 뒤 로그 한 줄을 쓰는 것을 담당함.
    def emit(self, record):
        today = date.today()
        # 자정이 지나면 열려 있던 파일을 닫고 새 날짜 파일로 바꿈
        if today != self.current_date:
            if self.stream:
                self.stream.close()
                self.stream = None   # 다음 emit 에서 새 파일이 열림
            self.current_date = today
            self.baseFilename = self._log_path_for(today)
        super().emit(record)


# 콘솔과 날짜별 로그 파일에 로그를 남기도록 설정하는 것을 담당함.
def setup_logging():
    """앱 시작 시 한 번 호출한다."""
    root_logger = logging.getLogger()
    # 두 번 설정되어 로그가 중복되는 것을 막음
    if getattr(root_logger, "_is_configured_by_app", False):
        return
    root_logger.setLevel(logging.INFO)
    server_formatter = logging.Formatter(SERVER_LOG_FORMAT)

    # 콘솔 출력
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(server_formatter)
    root_logger.addHandler(console_handler)

    # 서버 전체 로그 파일
    server_file_handler = DailyFileHandler("server")
    server_file_handler.setFormatter(server_formatter)
    root_logger.addHandler(server_file_handler)

    # 위반 기록은 고지서 형식 그대로(시간·레벨 머리말 없이) 별도 파일에도 남김
    violation_file_handler = DailyFileHandler("violation")
    violation_file_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger(VIOLATION_LOGGER_NAME).addHandler(violation_file_handler)

    # 웹 요청 로그(werkzeug)는 너무 많아서 경고 이상만 남김
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    root_logger._is_configured_by_app = True
