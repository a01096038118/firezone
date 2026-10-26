// Flask 서버 주소 (영상·이미지 서버). 서버에 올릴 때 이 값만 바꿈
const FLASK_BASE_URL = 'http://192.168.0.106:5000';

// admin 서버 주소 (탐지 사진은 admin 서버에 저장됨). 서버에 올릴 때 이 값만 바꿈
// admin-dev VM : 'http://192.168.56.103:8090'
// admin-prod VM : 'http://192.168.56.104:8090'
const ADMIN_BASE_URL = 'http://localhost:8090';
//const ADMIN_BASE_URL = 'http://192.168.56.103:8090';
//const ADMIN_BASE_URL = 'http://192.168.56.104:8090';

// 로그인 화면 주소
const LOGIN_URL = '/member/signin';

class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

// 비어 있는 값은 미확인으로 표시
function displayValue(value) {
    return value === null
    || value === undefined
    || String(value).trim() === ''
        ? '미확인'
        : String(value);
}

// 날짜를 화면에 표시할 형태로 변환
function formatTime(value) {
    if (!value) {
        return '미확인';
    }

    return String(value).replace('T', ' ').split('.')[0];
}

// 탐지 이미지 경로를 Flask 주소가 붙은 전체 주소로 변환
// (Flask 서버의 주소가 아니면 사용하지 않음)
function toImageUrl(path) {
    if (!path) {
        return '';
    }

    try {
        // admin이 저장한 사진(/uploads/detections/...)은 admin 서버에서,
        // 예전 기록(Flask 쪽 경로)은 Flask 서버에서 불러옴
        const base = String(path).trim().startsWith('/uploads/detections/')
            ? new URL(ADMIN_BASE_URL)
            : new URL(FLASK_BASE_URL);
        const url = new URL(path, base);

        return url.origin === base.origin ? url.href : '';
    } catch (error) {
        return '';
    }
}

// JSON 조회 공통 함수
async function fetchJson(url) {
    const response = await fetch(url, {
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin'
    });

    // 로그인 화면으로 이동된 경우도 로그인 필요로 처리
    if (response.redirected || response.status === 401) {
        throw new ApiError('로그인 상태를 확인해주세요.', 401);
    }

    if (response.status === 403) {
        throw new ApiError('조회 권한이 없습니다.', 403);
    }

    const contentType = response.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');

    if (!response.ok) {
        let message = '탐지 기록을 불러오지 못했습니다.';

        if (isJson) {
            try {
                const body = await response.json();
                if (body && body.message) {
                    message = body.message;
                }
            } catch (error) {
                // 본문을 읽지 못하면 기본 메시지 사용
            }
        }

        throw new ApiError(message, response.status);
    }

    if (!isJson) {
        throw new ApiError('서버의 데이터 응답을 확인해주세요.', 0);
    }

    return response.json();
}

// 표의 한 줄 전체를 눌러 탐지 상세 화면으로 이동 (관제 화면 최근 목록, 탐지 목록 공통)
// - 줄 안의 버튼(삭제 등)·링크를 누른 경우는 이동하지 않음
// - 키보드: Tab으로 줄 선택 후 Enter
function makeDetailRow(row, dlNo) {
    const url = `/dashboard/listDetail?dl_no=${encodeURIComponent(dlNo)}`;

    row.classList.add('clickable_row');
    row.tabIndex = 0;
    row.title = '상세 정보 보기';

    row.addEventListener('click', (event) => {
        if (event.target.closest('button, a, input, select')) {
            return;
        }
        window.location.href = url;
    });

    row.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && event.target === row) {
            window.location.href = url;
        }
    });
}
