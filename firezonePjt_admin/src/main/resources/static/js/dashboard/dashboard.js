document.addEventListener('DOMContentLoaded', () => {

    /*
     * Flask 팀원이 알려준 영상 주소를 넣기
     * 아래 영상 연결 코드는 <img>로 표시할 수 있는
     * MJPEG 스트림을 사용하는 경우의 코드
     */
    const STREAM_URL = `${FLASK_BASE_URL}/api/monitor`;

    // 영상 서버가 살아 있는지 확인하는 주소 (Flask 팀원에게 요청)
    // 비워 두면 영상 중단 감지를 하지 않음
    const STREAM_STATUS_URL = `${FLASK_BASE_URL}/api/health`;

    // 로그인 화면 주소. 비워 두면 안내 문구만 표시
    const LOGIN_URL = '/admin/signin';

    const REFRESH_MS = 5000;            // 탐지 목록 갱신 주기
    const STATUS_CHECK_MS = 10000;      // 영상 서버 확인 주기

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

    // 영상 서버 응답 확인 (영상이 중간에 끊긴 경우를 알아내기 위함)
    async function checkStreamStatus() {
        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 5000);

        try {
            // 다른 서버 주소라서 응답 내용은 읽지 않고 접속 여부만 확인
            await fetch(STREAM_STATUS_URL, {
                mode: 'no-cors',
                cache: 'no-store',
                signal: controller.signal
            });
        } catch (error) {
            liveStream.hidden = true;
            connectionStatus.textContent = '수신 중단';
            streamMessage.hidden = false;
            streamMessage.textContent =
                '영상 수신이 중단되었습니다. 재연결 버튼을 눌러주세요.';
        } finally {
            window.clearTimeout(timer);
        }
    }

    // ---------- 경보 ----------

    const alarmList = document.querySelector('#alarm_list');
    const soundButton = document.querySelector('#alarm_sound_btn');

    const MAX_ALARMS = 10;      // 화면에 보여줄 경보 최대 개수

    let lastDlNo = null;        // 마지막으로 확인한 탐지 번호 (처음 조회 때 기준값으로 저장)
    let soundOn = false;        // 경보 소리 사용 여부
    let audioContext = null;    // 소리를 만드는 브라우저 기능


    // 경보 소리 켜기/끄기 (브라우저 정책상 사용자가 한 번 눌러야 소리가 남)
    soundButton.addEventListener('click', () => {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        audioContext.resume();

        soundOn = !soundOn;
        soundButton.textContent = soundOn ? '경보 소리 끄기' : '경보 소리 켜기';

        // 켤 때 시험으로 한 번 울림
        if (soundOn) {
            playAlarmSound();
        }
    });
    const ALARM_REPEAT = 4;        // 울리는 횟수
    const ALARM_TONE_SEC = 0.7;    // 한 번 울리는 길이 (초)
    const ALARM_GAP_SEC = 0.3;     // 소리 사이 쉬는 시간 (초)
    const ALARM_FREQ = 880;        // 음 높이 (Hz, 낮을수록 묵직함 / 기존 880)
    const ALARM_VOLUME = 0.3;      // 음량 (0 ~ 1)

    function playAlarmSound() {
        if (!soundOn || !audioContext) {
            return;
        }

        const now = audioContext.currentTime;

        for (let i = 0; i < ALARM_REPEAT; i++) {
            const start = now + i * (ALARM_TONE_SEC + ALARM_GAP_SEC);
            const end = start + ALARM_TONE_SEC;

            // 기본음 + 한 옥타브 아래 저음(작게)
            const mainTone = audioContext.createOscillator();
            const subTone = audioContext.createOscillator();
            const gain = audioContext.createGain();
            const subGain = audioContext.createGain();

            mainTone.type = 'sawtooth';
            mainTone.frequency.value = ALARM_FREQ;

            subTone.type = 'sine';
            subTone.frequency.value = ALARM_FREQ / 2;
            subGain.gain.value = 0;      // 저음 크기 (0 = 없음, 1 = 원래 크기)

            // 시작·끝을 부드럽게 (뚝 끊기는 잡음 방지)
            gain.gain.setValueAtTime(0, start);
            gain.gain.linearRampToValueAtTime(ALARM_VOLUME, start + 0.05);
            gain.gain.setValueAtTime(ALARM_VOLUME, end - 0.1);
            gain.gain.linearRampToValueAtTime(0, end);

            // 연결: 기본음 → gain, 저음 → subGain → gain → 스피커
            mainTone.connect(gain);
            subTone.connect(subGain);
            subGain.connect(gain);
            gain.connect(audioContext.destination);

            mainTone.start(start);
            subTone.start(start);
            mainTone.stop(end);
            subTone.stop(end);
        }
    }

    // 경보 문구 (2026-10-21T15:30:12 → "15시 30분 12초에 Z01 구역에서 주정차 발생")
    function alarmMessage(dto) {
        const value = String(dto.dl_first_detected_at || '');
        const time = value.includes('T')
            ? value.split('T')[1].split('.')[0]
            : '';

        const [hour, minute, second] = time.split(':');

        const timeText = hour
            ? `${hour}시 ${minute}분 ${second}초`
            : '시간 미확인';

        return `${timeText}에 ${displayValue(dto.dl_zone_no)} 구역에서 주정차 발생`;
    }

    // 경보 목록 맨 위에 추가 (누르면 상세 화면 = 경보 내용 조회)
    function addAlarm(dto) {
        const item = document.createElement('li');
        const link = document.createElement('a');

        link.href =
            `/dashboard/listDetail?dl_no=${encodeURIComponent(dto.dl_no)}`;
        link.textContent = alarmMessage(dto);

        item.appendChild(link);
        alarmList.prepend(item);

        // 오래된 경보는 지움
        while (alarmList.children.length > MAX_ALARMS) {
            alarmList.lastElementChild.remove();
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

        newDetections.forEach(addAlarm);
        playAlarmSound();

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
        // 주소를 비운 상태의 오류는 무시
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

        /*
         * 위쪽 camera_info는 영상 소스 정보이므로
         * 최신 탐지 기록의 카메라 정보로 덮어쓰지 않음.
         */

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

        cell.colSpan = 5;
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
                if (index === 0) {
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
        const data = await fetchJson(
            '/detections/list?page=1&size=10&direction=desc'
        );

        if (!data || !Array.isArray(data.content)) {
            throw new ApiError('탐지 목록 응답 형식이 올바르지 않습니다.', 0);
        }

        const detections = data.content;
        hasData = true;

        if (detections.length === 0) {

            // 기록이 하나도 없을 때는 0을 기준으로 → 첫 탐지부터 경보
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

            // 처음부터 실패했다면 목록 영역에도 안내
            if (!hasData) {
                showListMessage(error.message);
            }

            // 로그인·권한 문제는 계속 요청해도 소용없으므로 갱신을 멈춤
            if (error.status === 401 || error.status === 403) {
                stopped = true;

                if (error.status === 401 && LOGIN_URL) {
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

    if (STREAM_STATUS_URL) {
        window.setInterval(checkStreamStatus, STATUS_CHECK_MS);
    }
});