"""Boot 서버 HTTP 호출 (Boot 관리자 앱 firezonePjt_admin 의 DetectionController 기준).

POST /detections          → 탐지 기록 저장 (같은 날 같은 차면 Boot가 갱신), 응답 {"dl_no": 15, "result": "CREATED"}
                            사진을 함께 보낼 때는 multipart: data(JSON) + image(단속 사진 파일)
PUT  /detections/{dl_no}  → 탐지 기록 수정 (Boot에 아직 없음, config.BOOT_UPDATE_API_READY 로 켬)
"""
import json
import logging
import os
import re

import requests

import config

log = logging.getLogger(__name__)

# Boot 화면(Thymeleaf 폼)에 숨어 있는 CSRF 토큰 <input type="hidden" name="_csrf" value="...">
CSRF_TOKEN_PATTERN = re.compile(r'name="_csrf"[^>]*value="([^"]+)"|value="([^"]+)"[^>]*name="_csrf"')
# Spring Security 가 CSRF 토큰을 읽는 기본 헤더 이름
CSRF_HEADER_NAME = "X-CSRF-TOKEN"
# 사진과 함께 보낼 때 multipart 파트 이름 (Boot DetectionController @RequestPart 기준)
MULTIPART_DATA_PART = "data"     # 기록 JSON
MULTIPART_IMAGE_PART = "image"   # 단속 사진 파일

# 세션 쿠키(JSESSIONID)와 CSRF 토큰을 계속 쓰기 위한 연결 (전송 스레드 한 개만 사용)
_boot_session = requests.Session()


# Boot 탐지 API 주소를 만드는 것을 담당함.
def _detection_api_url(dl_no=None):
    base_url = config.BOOT_URL.rstrip("/") + config.BOOT_DETECTION_API_PATH
    # 수정할 때는 주소 끝에 기록번호를 붙임
    return f"{base_url}/{dl_no}" if dl_no is not None else base_url


# Boot 응답에서 탐지 기록번호(dl_no)를 꺼내는 것을 담당함.
def _read_dl_no(response):
    """Boot는 숫자만 돌려준다 (예: 15). JSON {"dl_no": 15} 형식이 와도 읽는다. 못 읽으면 None."""
    response_text = response.text.strip()
    # 숫자만 온 경우 (지금 Boot 방식)
    if response_text.isdigit():
        return int(response_text)
    # JSON 객체로 온 경우 (나중에 Boot 응답이 바뀌어도 동작하도록)
    try:
        response_body = response.json()
    except ValueError:
        return None
    if isinstance(response_body, dict):
        for id_field in ("dl_no", "dlNo", "id"):
            if response_body.get(id_field) is not None:
                return int(response_body[id_field])
    return None


# Boot 화면에서 CSRF 토큰을 받아 이후 요청에 붙이는 것을 담당함.
def _refresh_csrf_token():
    """Boot가 /detections 를 CSRF 검사에서 빼주기 전까지 쓰는 임시 방법. 성공하면 True."""
    # 토큰이 들어 있는 Boot 화면을 같은 세션으로 열어서 세션 쿠키와 토큰을 함께 받음
    token_page_url = config.BOOT_URL.rstrip("/") + config.BOOT_CSRF_TOKEN_PAGE_PATH
    page = _boot_session.get(token_page_url, timeout=config.BOOT_REQUEST_TIMEOUT_SECONDS)
    token_match = CSRF_TOKEN_PATTERN.search(page.text)
    if not token_match:
        log.error("Boot 화면(%s)에서 CSRF 토큰을 찾지 못함", token_page_url)
        return False
    # 찾은 토큰을 이후 모든 요청 헤더에 붙임
    _boot_session.headers[CSRF_HEADER_NAME] = token_match.group(1) or token_match.group(2)
    log.info("Boot CSRF 토큰을 받아 요청에 붙임 (Boot에 CSRF 예외 설정이 없어서 사용하는 임시 방법)")
    return True


# Boot 요청을 보내고 CSRF로 막히면(403) 토큰을 받아 한 번 더 보내는 것을 담당함.
def _send_with_csrf_retry(method, url, payload, image_file=None):
    """image_file 이 있으면 multipart(data JSON + image 파일), 없으면 JSON 으로 보낸다."""
    # 같은 요청을 다시 보낼 수 있게 요청 내용을 만드는 함수로 둠 (파일은 보낼 때마다 새로 읽음)
    def send():
        if image_file is None:
            body = {"json": payload}
        else:
            with open(image_file, "rb") as image:
                image_bytes = image.read()
            body = {"files": {
                MULTIPART_DATA_PART: (None, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                      "application/json"),
                MULTIPART_IMAGE_PART: (os.path.basename(image_file), image_bytes, "image/jpeg"),
            }}
        # 로그인 화면으로 돌려보내는 응답(302)을 따라가면 저장 성공처럼 보이므로 따라가지 않음
        return _boot_session.request(method, url, timeout=config.BOOT_REQUEST_TIMEOUT_SECONDS,
                                     allow_redirects=False, **body)

    response = send()
    # 403 이면 CSRF 토큰 문제일 가능성이 커서 토큰을 받아 다시 보냄
    if response.status_code == 403 and _refresh_csrf_token():
        response = send()
    # 다른 주소로 돌려보내면(보통 로그인 화면) 저장되지 않은 것이므로 실패로 처리
    if response.is_redirect:
        raise requests.HTTPError(
            f"Boot가 {response.headers.get('Location')} 로 돌려보냄 (로그인 필요 → 저장 안 됨). "
            f"Boot 보안 설정에서 {method} /detections 를 로그인 없이 허용해야 함", response=response)
    return response


# Boot에 새 탐지 기록 저장 요청(POST /detections)을 담당함.
def post_detection(payload, image_file=None):
    """탐지 기록 저장 → Boot가 만든(또는 갱신한) 기록번호 dl_no (못 읽으면 None). 실패 시 requests 예외.
    image_file: 함께 보낼 단속 사진 파일 경로 (사진을 Boot에 넘기는 방식일 때)"""
    response = _send_with_csrf_retry("POST", _detection_api_url(), payload, image_file)
    # 400·403·500 등이면 예외로 올려서 전송 스레드가 로그를 남기게 함
    response.raise_for_status()
    return _read_dl_no(response)


# Boot에 탐지 기록 수정 요청(PUT /detections/{dl_no})을 담당함.
def put_detection(dl_no, payload):
    """기존 탐지 기록 수정. 기록이 없으면(관리자가 삭제) False, 성공하면 True. 그 밖의 실패는 requests 예외."""
    response = _send_with_csrf_retry("PUT", _detection_api_url(dl_no), payload)
    # 관리자가 기록을 지운 경우 → 호출한 쪽에서 새로 저장하도록 알림
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True


# Boot 서버 연결 상태 확인을 담당함.
def check_boot_connection():
    """Boot 서버 연결 상태: "disabled" / "ok" / "unreachable"."""
    # Boot 전송을 꺼둔 경우
    if not config.BOOT_ENABLED:
        return "disabled"
    # Boot 첫 화면에 접속되는지만 확인
    try:
        requests.get(config.BOOT_URL, timeout=config.BOOT_REQUEST_TIMEOUT_SECONDS)
        return "ok"
    except requests.RequestException:
        return "unreachable"
