// Flask 서버 주소 (이미지·영상을 제공하는 서버). 팀원에게 확인 후 입력
// 예: 'http://192.168.56.xx:5000'
const FLASK_BASE_URL = 'http://192.168.0.106:5000';

// 서버 오류를 상태 코드와 함께 전달하는 오류 클래스
class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

// 값이 없으면 미확인 표시
function displayValue(value) {
    if (value === null
        || value === undefined
        || String(value).trim() === '') {
        return '미확인';
    }

    return String(value);
}

// 날짜 표시 형식 변경 (2026-10-19T10:30:00.123 → 2026-10-19 10:30:00)
function formatTime(value) {
    if (!value) {
        return '미확인';
    }

    return String(value).replace('T', ' ').split('.')[0];
}

// Spring Security를 쓸 때 POST/DELETE에 필요한 CSRF 토큰 헤더
// (HTML head에 _csrf, _csrf_header meta 태그가 있을 때만 동작, 5단계에서 연결)
function csrfHeaders() {
    const token = document.querySelector('meta[name="_csrf"]');
    const header = document.querySelector('meta[name="_csrf_header"]');

    if (token && header) {
        return { [header.content]: token.content };
    }

    return {};
}

// 서버에 요청하고 JSON을 돌려줌
// 실패하면 서버가 보낸 message를 담은 ApiError를 던짐
// 본문이 JSON이 아니면 null을 돌려줌 (삭제 성공 응답 등)
async function fetchJson(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();

    const response = await fetch(url, {
        ...options,
        headers: {
            'Accept': 'application/json',
            ...(method === 'GET' ? {} : csrfHeaders()),
            ...(options.headers || {})
        }
    });

    // Security가 로그인 화면으로 보낸 경우도 로그인 문제로 처리
    if (response.redirected || response.status === 401) {
        throw new ApiError('로그인 상태를 확인해주세요.', 401);
    }

    if (response.status === 403) {
        throw new ApiError('권한이 없습니다.', 403);
    }

    if (!response.ok) {
        let message = '요청을 처리하지 못했습니다.';

        try {
            const body = await response.json();
            if (body && body.message) {
                message = body.message;
            }
        } catch (error) {
            // 본문이 JSON이 아니면 기본 문구 사용
        }

        throw new ApiError(message, response.status);
    }

    const contentType = response.headers.get('content-type') || '';

    if (!contentType.includes('application/json')) {
        return null;
    }

    return response.json();
}

// DB에 저장된 이미지 경로를 브라우저에서 열 수 있는 주소로 변환
// 안전하지 않거나 열 수 없는 값이면 빈 문자열을 반환 (이미지 없음으로 처리)
function toImageUrl(path) {
    if (!path || typeof path !== 'string') {
        return '';
    }

    const trimmed = path.trim();

    // 빈 값, 상위 폴더 이동(..)이 들어간 값은 사용하지 않음
    if (trimmed === '' || trimmed.includes('..')) {
        return '';
    }

    const base = FLASK_BASE_URL || window.location.origin;

    let url;
    try {
        url = new URL(trimmed, base);
    } catch (error) {
        return '';
    }

    // http, https만 허용 (C:\... 같은 서버 폴더 경로는 여기서 걸러짐)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return '';
    }

    // 정해 둔 서버의 이미지만 허용 (임의 주소 차단)
    if (url.origin !== new URL(base).origin) {
        return '';
    }

    return url.href;
}