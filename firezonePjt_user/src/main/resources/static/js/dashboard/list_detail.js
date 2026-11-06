document.addEventListener('DOMContentLoaded', async () => {

    // 상세 화면 주소에서 탐지 번호 가져오기
    // 예: /dashboard/listDetail?dl_no=5
    const params = new URLSearchParams(window.location.search);
    const dlNo = params.get('dl_no');

    const detectionImage = document.querySelector('#detection_img');

    // 이미지 안내 문구
    const imageMessage = document.createElement('p');
    imageMessage.textContent = '이미지를 불러오는 중입니다.';
    document.querySelector('.detection_img').appendChild(imageMessage);

    // 오류 안내 문구 (제목 아래)
    const errorMessage = document.createElement('p');
    errorMessage.hidden = true;
    document.querySelector('.list h2').after(errorMessage);

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.hidden = false;

        imageMessage.textContent = '탐지 이미지가 없습니다.';
    }

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

    // 주정차 시간 문구 (예: 12분 30초)
    function formatDuration(first, last) {
        const start = new Date(String(first).split('.')[0]);
        const end = new Date(String(last).split('.')[0]);

        if (isNaN(start) || isNaN(end) || end < start) {
            return '미확인';
        }

        const totalSeconds = Math.floor((end - start) / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        if (hours > 0) {
            return `${hours}시간 ${minutes}분`;
        }
        if (minutes > 0) {
            return `${minutes}분 ${seconds}초`;
        }
        return `${seconds}초`;
    }

    // 요약 문구용 날짜 (예: 2026년 10월 23일 17시 50분)
    function formatKoreanDate(value) {
        const date = new Date(String(value).split('.')[0]);

        if (isNaN(date)) {
            return '';
        }

        return `${date.getFullYear()}년 ${date.getMonth() + 1}월 `
            + `${date.getDate()}일 ${date.getHours()}시 ${date.getMinutes()}분`;
    }

    // 탐지 번호 확인 (숫자만 허용)
    if (!dlNo || !/^\d+$/.test(dlNo)) {
        showError('탐지 번호가 올바르지 않습니다.');
        return;
    }

    try {
        const dto = await fetchJson(
            `/detections/detail?dl_no=${encodeURIComponent(dlNo)}`
        );

        // HTML의 각 위치에 데이터 표시
        document.querySelector('#detection_no').textContent =
            displayValue(dto.dl_no);

        document.querySelector('#camera_id').textContent =
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

        // 주정차 시간 = 마지막 탐지 시간 - 최초 탐지 시간
        const duration = formatDuration(
            dto.dl_first_detected_at, dto.dl_last_detected_at);

        document.querySelector('#duration').textContent = duration;

        // 요약 문구 (차량번호와 주정차 시간은 강조, textContent로 넣어 HTML로 해석되지 않게 함)
        const startText = formatKoreanDate(dto.dl_first_detected_at);

        if (startText && dto.dl_car_number && duration !== '미확인') {
            const car = document.createElement('strong');
            car.textContent = dto.dl_car_number;

            const time = document.createElement('strong');
            time.textContent = duration;

            document.querySelector('#summary_message').replaceChildren(
                `${startText} `, car, ' 차량 ', time, ' 동안 주정차로 판단됩니다.'
            );
        }

        // 이미지 주소가 있으면 사진 표시 (admin 저장 사진은 admin 서버, 예전 기록은 Flask)
        const imageUrl = toImageUrl(dto.dl_image_path);

        if (imageUrl) {
            detectionImage.src = imageUrl;
        } else {
            imageMessage.textContent = '탐지 이미지가 없습니다.';
        }

    } catch (error) {
        console.error(error);
        showError(error.message);

        if (error.status === 401) {
            window.location.href = LOGIN_URL;
        }
    }
});