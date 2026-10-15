document.addEventListener('DOMContentLoaded', () => {

    const listBody = document.querySelector('#detection_log_list');

    // 값이 없으면 미확인 표시
    function displayValue(value) {
        if (value === null
            || value === undefined
            || String(value).trim() === '') {
            return '미확인';
        }

        return String(value);
    }

    // 날짜 표시 형식 변경
    function formatTime(value) {
        if (!value) {
            return '미확인';
        }

        return value.replace('T', ' ').split('.')[0];
    }

    // 로딩·빈 목록·오류 메시지 표시
    function showMessage(message) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');

        cell.colSpan = 5;
        cell.textContent = message;

        row.appendChild(cell);
        listBody.replaceChildren(row);
    }

    // 조회한 목록을 표에 표시
    function showDetections(detections) {
        listBody.replaceChildren();

        for (const dto of detections) {
            const row = document.createElement('tr');

            // 구역번호를 누르면 해당 기록의 상세 화면으로 이동
            const zoneCell = document.createElement('td');
            const detailLink = document.createElement('a');

            detailLink.href =
                `/dashboard/listDetail?dl_no=${encodeURIComponent(dto.dl_no)}`;

            detailLink.textContent = displayValue(dto.dl_zone_no);

            zoneCell.appendChild(detailLink);
            row.appendChild(zoneCell);

            // 나머지 네 개의 열
            const values = [
                displayValue(dto.dl_violation_type),
                displayValue(dto.dl_car_number),
                formatTime(dto.dl_first_detected_at),
                formatTime(dto.dl_last_detected_at)
            ];

            for (const value of values) {
                const cell = document.createElement('td');

                cell.textContent = value;
                row.appendChild(cell);
            }

            listBody.appendChild(row);
        }
    }

    // 서버에서 탐지 목록 조회
    async function fetchDetectionList() {
        showMessage('탐지 기록을 불러오는 중입니다.');

        try {
            const response = await fetch(
                '/detections/list?page=0&size=20&direction=desc',
                {
                    headers: {
                        'Accept': 'application/json'
                    }
                }
            );

            if (response.redirected || response.status === 401) {
                throw new Error('로그인 상태를 확인해주세요.');
            }

            if (response.status === 403) {
                throw new Error('탐지 목록 조회 권한이 없습니다.');
            }

            if (!response.ok) {
                throw new Error('탐지 목록 조회에 실패했습니다.');
            }

            const contentType =
                response.headers.get('content-type') || '';

            if (!contentType.includes('application/json')) {
                throw new Error('서버의 데이터 응답을 확인해주세요.');
            }

            const detections = await response.json();

            if (!Array.isArray(detections)) {
                throw new Error('탐지 목록 응답 형식이 올바르지 않습니다.');
            }

            if (detections.length === 0) {
                showMessage('저장된 탐지 기록이 없습니다.');
                return;
            }

            showDetections(detections);

        } catch (error) {
            console.error('탐지 목록 조회 오류:', error);
            showMessage(error.message);
        }
    }

    fetchDetectionList();
});