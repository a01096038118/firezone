document.addEventListener('DOMContentLoaded', () => {

    /*
     * Flask 팀원이 알려준 영상 주소를 넣기
     * 아래 영상 연결 코드는 <img>로 표시할 수 있는
     * MJPEG 스트림을 사용하는 경우의 코드
     */
    const STREAM_URL = '';

    const liveStream = document.querySelector('#live_stream');
    const streamMessage = document.querySelector('#stream_message');
    const connectionStatus =
        document.querySelector('.connection_status');

    const cameraId = document.querySelector('.camera_id');
    const cameraZone = document.querySelector('.zone_no');

    const detectionImage = document.querySelector('#detection_img');
    const detailLink =
        document.querySelector('#detection_detail_link');

    const listBody = document.querySelector('#detection_log_list');

    // 날짜를 화면에 표시할 형태로 변환
    function formatTime(value) {
        if (!value) {
            return '미확인';
        }

        return value.replace('T', ' ').split('.')[0];
    }

    // 비어 있는 값은 미확인으로 표시
    function displayValue(value) {
        return value === null
        || value === undefined
        || String(value).trim() === ''
            ? '미확인'
            : String(value);
    }

    // 실시간 영상 연결
    function connectStream() {
        if (!STREAM_URL) {
            connectionStatus.textContent = '영상 주소 미설정';
            streamMessage.textContent =
                'Flask 영상 주소를 설정해주세요.';
            return;
        }

        connectionStatus.textContent = '연결 시도 중';
        streamMessage.textContent = '영상을 연결하고 있습니다.';
        streamMessage.hidden = false;

        liveStream.hidden = false;
        liveStream.src = STREAM_URL;
    }

    liveStream.addEventListener('load', () => {
        connectionStatus.textContent = '영상 응답 수신';
        streamMessage.hidden = true;
    });

    liveStream.addEventListener('error', () => {
        liveStream.hidden = true;
        connectionStatus.textContent = '연결 실패';
        streamMessage.hidden = false;
        streamMessage.textContent =
            '영상 연결에 실패했습니다. 재연결 버튼을 눌러주세요.';
    });

    // 재연결 버튼 생성
    const reconnectButton = document.createElement('button');
    reconnectButton.type = 'button';
    reconnectButton.textContent = '영상 재연결';

    document.querySelector('.stream_area')
        .appendChild(reconnectButton);

    reconnectButton.addEventListener('click', () => {
        liveStream.removeAttribute('src');
        connectStream();
    });

    // 탐지 이미지가 없거나 열리지 않는 경우 안내
    const imageMessage = document.createElement('p');
    imageMessage.textContent = '탐지된 이미지가 없습니다.';

    document.querySelector('.detection_img')
        .appendChild(imageMessage);

    detectionImage.addEventListener('load', () => {
        detectionImage.hidden = false;
        imageMessage.hidden = true;
    });

    detectionImage.addEventListener('error', () => {
        detectionImage.hidden = true;
        imageMessage.hidden = false;
        imageMessage.textContent = '탐지된 이미지를 불러올 수 없습니다.';
    });

    // 실시간 탐지 정보 표시
    function showLatestDetection(dto) {
        document.querySelector('#zone_id').textContent =
            displayValue(dto.dl_zone_no);

        document.querySelector('#violation_type').textContent =
            displayValue(dto.dl_violation_type);

        document.querySelector('#car_number').textContent =
            displayValue(dto.dl_car_number);

        document.querySelector('#first_detected').textContent =
            formatTime(dto.dl_first_detected_at);

        document.querySelector('#last_detected').textContent =
            formatTime(dto.dl_last_detected_at);

        /*
         * 위쪽 camera_info는 영상 소스 정보이므로
         * 최신 탐지 기록의 카메라 정보로 덮어쓰지 않음.
         */

        if (dto.dl_image_path) {
            // 같은 경로의 이미지는 반복해서 다시 요청하지 않음
            if (detectionImage.getAttribute('src')
                !== dto.dl_image_path) {

                detectionImage.hidden = true;
                imageMessage.hidden = false;
                imageMessage.textContent = '이미지를 불러오는 중입니다.';
                detectionImage.src = dto.dl_image_path;
            }
        } else {
            detectionImage.removeAttribute('src');
            detectionImage.hidden = true;
            imageMessage.hidden = false;
            imageMessage.textContent = '탐지 이미지가 없습니다.';
        }

        detailLink.href =
            `/dashboard/listDetail?dl_no=${encodeURIComponent(dto.dl_no)}`;

        detailLink.hidden = false;
    }

    // 목록 안내 메시지 표시
    function showListMessage(message) {
        listBody.replaceChildren();

        const row = document.createElement('tr');
        const cell = document.createElement('td');

        cell.colSpan = 5;
        cell.textContent = message;

        row.appendChild(cell);
        listBody.appendChild(row);
    }

    // 탐지 기록이 없는 경우
    function clearLatestDetection() {
        [
            '#zone_id',
            '#violation_type',
            '#car_number',
            '#first_detected',
            '#last_detected'
        ].forEach(selector => {
            document.querySelector(selector).textContent = '-';
        });

        detectionImage.removeAttribute('src');
        detectionImage.hidden = true;

        imageMessage.hidden = false;
        imageMessage.textContent = '탐지 이미지가 없습니다.';

        detailLink.hidden = true;
        detailLink.removeAttribute('href');
    }

    // 최근 탐지 목록 표시
    function showDetectionList(detections) {
        listBody.replaceChildren();

        for (const dto of detections) {
            const row = document.createElement('tr');

            const values = [
                dto.dl_no,
                dto.dl_camera_id,
                dto.dl_zone_no,
                dto.dl_car_number,
                formatTime(dto.dl_first_detected_at)
            ];

            values.forEach((value, index) => {
                const cell = document.createElement('td');

                // 탐지 번호를 누르면 상세 화면 이동
                if (index === 1) {
                    const link = document.createElement('a');

                    link.href =
                        `/dashboard/listDetail?dl_no=${encodeURIComponent(dto.dl_no)}`;

                    link.textContent = displayValue(value);
                    cell.appendChild(link);
                } else {
                    cell.textContent = displayValue(value);
                }

                row.appendChild(cell);
            });

            listBody.appendChild(row);
        }
    }

    // 최신 10건 조회
    async function fetchDetections() {
        const response = await fetch(
            '/detections/list?page=0&size=10&direction=desc',
            {
                headers: {
                    'Accept': 'application/json'
                }
            }
        );

        // Security가 로그인 화면으로 이동시킨 경우도 확인
        if (response.redirected || response.status === 401) {
            throw new Error('로그인 상태를 확인해주세요.');
        }

        if (response.status === 403) {
            throw new Error('탐지 목록 조회 권한이 없습니다.');
        }

        if (!response.ok) {
            throw new Error('탐지 기록을 불러오지 못했습니다.');
        }

        const contentType = response.headers.get('content-type') || '';

        if (!contentType.includes('application/json')) {
            throw new Error('서버의 데이터 응답을 확인해주세요.');
        }

        const data = await response.json();
        const detections = data.content;

        if (!Array.isArray(detections)) {
            throw new Error('탐지 목록 응답 형식이 올바르지 않습니다.');
        }

        if (detections.length === 1) {
            showListMessage('저장된 탐지 기록이 없습니다.');
            clearLatestDetection();
            return;
        }

        showLatestDetection(detections[0]);
        showDetectionList(detections);
    }

    // 조회 오류 안내
    const refreshMessage = document.createElement('p');
    refreshMessage.hidden = true;
    listBody.closest('table').after(refreshMessage);

    // 한 요청이 끝난 후 5초 뒤 다시 조회
    async function refreshDetections() {
        try {
            await fetchDetections();
            refreshMessage.hidden = true;
        } catch (error) {
            console.error(error);

            refreshMessage.textContent = error.message;
            refreshMessage.hidden = false;
        } finally {
            window.setTimeout(refreshDetections, 5000);
        }
    }

    // 영상 소스 정보는 Flask 연동 시 실제 값으로 설정
    cameraId.textContent = '-';
    cameraZone.textContent = '-';

    connectStream();
    refreshDetections();
});