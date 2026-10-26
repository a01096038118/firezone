document.addEventListener('DOMContentLoaded', () => {

    // Flask 영상 스트림 (common.js의 FLASK_BASE_URL 사용)
    const STREAM_URL = `${FLASK_BASE_URL}/api/monitor`;

    const REFRESH_MS = 5000;        // 탐지 목록 갱신 주기

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

    let stopped = false;        // 로그인·권한 문제로 갱신을 멈췄는지
    let hasData = false;        // 목록을 한 번이라도 불러왔는지


    // ---------- 실시간 영상 ----------

    function connectStream() {
        connectionStatus.textContent = '연결 시도 중';
        streamMessage.textContent = '영상을 연결하고 있습니다.';
        streamMessage.hidden = false;

        // 매번 새 연결이 되도록 주소 끝에 시간 값을 붙임
        const separator = STREAM_URL.includes('?') ? '&' : '?';

        liveStream.hidden = false;
        liveStream.src = `${STREAM_URL}${separator}t=${Date.now()}`;
    }

    liveStream.addEventListener('load', () => {
        connectionStatus.textContent = '영상 응답 수신';
        streamMessage.hidden = true;
    });

    liveStream.addEventListener('error', () => {
        // 주소를 비운 상태의 오류는 무시
        if (!liveStream.getAttribute('src')) {
            return;
        }

        liveStream.hidden = true;
        connectionStatus.textContent = '연결 실패';
        streamMessage.hidden = false;
        streamMessage.textContent =
            '영상 연결에 실패했습니다. 재연결 버튼을 눌러주세요.';
    });

    // 재연결 버튼
    const reconnectButton = document.createElement('button');
    reconnectButton.type = 'button';
    reconnectButton.textContent = '영상 재연결';

    document.querySelector('.stream_area')
        .appendChild(reconnectButton);

    reconnectButton.addEventListener('click', () => {
        liveStream.removeAttribute('src');
        connectStream();
    });

    // ---------- 경보 ----------
    let lastDlNo = null;        // 마지막으로 확인한 탐지 번호 (처음 조회 때 기준값으로 저장)

    // 경보 소리·팝업은 모든 화면 공통 기능(js/dashboard/alarm.js)이 처리
    function notifyAlarm(newDetections) {
        if (window.FirezoneAlarm) {
            window.FirezoneAlarm.notify(newDetections);
        }
    }


    // 새로 들어온 탐지가 있으면 경보 발생
    function checkNewDetections(detections) {
        const newestDlNo = Number(detections[0].dl_no);

        // 처음 조회한 기록은 경보로 보지 않고 기준값으로만 저장
        if (lastDlNo === null) {
            lastDlNo = newestDlNo;
            return;
        }

        // 기준값보다 큰 번호 = 새 탐지 (오래된 것부터 추가)
        const newDetections = detections
            .filter(dto => Number(dto.dl_no) > lastDlNo)
            .reverse();

        if (newDetections.length === 0) {
            return;
        }

        notifyAlarm(newDetections);

        lastDlNo = newestDlNo;
    }


    // ---------- 탐지 정보 ----------

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
        if (!detectionImage.getAttribute('src')) {
            return;
        }

        detectionImage.hidden = true;
        imageMessage.hidden = false;
        imageMessage.textContent = '탐지된 이미지를 불러올 수 없습니다.';
    });

    // 최신 탐지 정보 표시
    function showLatestDetection(dto) {
        document.querySelector('#detection_camera_id').textContent =
            displayValue(dto.dl_camera_id);

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

        const imageUrl = toImageUrl(dto.dl_image_path);

        if (imageUrl) {
            // 같은 주소의 이미지는 반복해서 다시 요청하지 않음
            if (detectionImage.getAttribute('src') !== imageUrl) {
                detectionImage.hidden = true;
                imageMessage.hidden = false;
                imageMessage.textContent = '이미지를 불러오는 중입니다.';
                detectionImage.src = imageUrl;
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

        cell.colSpan = 4;
        cell.textContent = message;

        row.appendChild(cell);
        listBody.appendChild(row);
    }

    // 탐지 기록이 없는 경우
    function clearLatestDetection() {
        [
            '#detection_camera_id',
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
    // 최근 탐지 목록 (번호 열 없음, 줄을 누르면 상세 화면으로 이동)
    function showDetectionList(detections) {
        listBody.replaceChildren();

        for (const dto of detections) {
            const row = document.createElement('tr');

            const values = [
                dto.dl_camera_id,
                dto.dl_zone_no,
                dto.dl_car_number,
                formatTime(dto.dl_first_detected_at)
            ];

            for (const value of values) {
                const cell = document.createElement('td');
                cell.textContent = displayValue(value);
                row.appendChild(cell);
            }

            makeDetailRow(row, dto.dl_no);
            listBody.appendChild(row);
        }
    }

    // 최신 10건 조회
    async function fetchDetections() {
        const data = await fetchJson(
            '/detections/list?page=1&size=10&direction=desc'
        );

        // 서버 응답: { content: [...], totalElements, ... }
        if (!data || !Array.isArray(data.content)) {
            throw new ApiError('탐지 목록 응답 형식이 올바르지 않습니다.', 0);
        }

        const detections = data.content;
        hasData = true;

        if (detections.length === 0) {

            if (lastDlNo === null) {
                lastDlNo = 0;
            }

            showListMessage('저장된 탐지 기록이 없습니다.');
            clearLatestDetection();
            return;
        }
        checkNewDetections(detections);

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

            if (!hasData) {
                showListMessage(error.message);
            }

            // 로그인·권한 문제는 계속 요청해도 소용없으므로 멈춤
            if (error.status === 401 || error.status === 403) {
                stopped = true;

                if (error.status === 401) {
                    window.location.href = LOGIN_URL;
                }

                return;
            }
        }

        if (!stopped) {
            window.setTimeout(refreshDetections, REFRESH_MS);
        }
    }

    // 영상 소스 정보는 Flask 연동 시 실제 값으로 설정
    cameraId.textContent = '-';
    cameraZone.textContent = '-';

    connectStream();
    refreshDetections();
});