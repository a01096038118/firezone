document.addEventListener('DOMContentLoaded', async () => {

    const message = document.getElementById('detail_message');
    const content = document.getElementById('detail_content');
    const image = document.getElementById('detection_img');
    const imageMessage = document.getElementById('image_message');
    const deleteButton = document.getElementById('delete_button');

    // 화면에 안내 문구만 보여주고 정보 영역은 숨김
    function showError(text) {
        message.textContent = text;
        message.hidden = false;
        content.hidden = true;
    }

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

    // 요약 문구용 날짜 (예: 2026년 10월 19일 10시 30분)
    function formatKoreanDate(value) {
        const date = new Date(String(value).split('.')[0]);

        if (isNaN(date)) {
            return '';
        }

        return `${date.getFullYear()}년 ${date.getMonth() + 1}월 `
            + `${date.getDate()}일 ${date.getHours()}시 ${date.getMinutes()}분`;
    }

    // 이미지 표시 (없거나 열리지 않으면 안내 문구)
    function showImage(path) {
        const imageUrl = toImageUrl(path);

        image.addEventListener('load', () => {
            image.hidden = false;
            imageMessage.hidden = true;
        });

        image.addEventListener('error', () => {
            image.hidden = true;
            imageMessage.hidden = false;
            imageMessage.textContent = '탐지된 이미지를 불러올 수 없습니다.';
        });

        if (!imageUrl) {
            image.hidden = true;
            imageMessage.hidden = false;
            imageMessage.textContent = '탐지된 이미지가 없습니다.';
            return;
        }

        image.src = imageUrl;
    }

    // 상세 화면 주소에서 탐지 번호 가져오기
    // 예: /dashboard/listDetail?dl_no=5
    const params = new URLSearchParams(window.location.search);
    const dlNo = params.get('dl_no');

    if (!dlNo) {
        showError('탐지 번호가 없습니다.');
        return;
    }

    try {
        const dto = await fetchJson(
            `/detections/detail?dl_no=${encodeURIComponent(dlNo)}`
        );

        if (!dto) {
            throw new ApiError('탐지 정보 응답 형식이 올바르지 않습니다.', 0);
        }

        document.getElementById('detection_no').textContent =
            displayValue(dto.dl_no);

        document.getElementById('camera_id').textContent =
            displayValue(dto.dl_camera_id);

        document.getElementById('zone_id').textContent =
            displayValue(dto.dl_zone_no);

        document.getElementById('violation_type').textContent =
            displayValue(dto.dl_violation_type);

        document.getElementById('car_number').textContent =
            displayValue(dto.dl_car_number);

        document.getElementById('first_detected').textContent =
            formatTime(dto.dl_first_detected_at);

        document.getElementById('last_detected').textContent =
            formatTime(dto.dl_last_detected_at);

        const duration = formatDuration(
            dto.dl_first_detected_at, dto.dl_last_detected_at);

        document.getElementById('duration').textContent = duration;

        // 요약 문구: 2026년 10월 19일 10시 30분 12가3456 차량 12분 30초 동안 주정차로 판단됩니다.
        const startText = formatKoreanDate(dto.dl_first_detected_at);

        if (startText && dto.dl_car_number && duration !== '미확인') {
            const summary = document.getElementById('summary_message');

            // 차량번호와 주정차 시간은 강조 표시 (textContent로 넣어 HTML로 해석되지 않게 함)
            const car = document.createElement('strong');
            car.textContent = dto.dl_car_number;

            const time = document.createElement('strong');
            time.textContent = duration;

            summary.replaceChildren(
                `${startText} `, car, ' 차량 ', time, ' 동안 주정차로 판단됩니다.'
            );
        }

        showImage(dto.dl_image_path);

        message.hidden = true;
        content.hidden = false;

    } catch (error) {
        console.error(error);

        // 상태별 안내 문구
        if (error.status === 404) {
            showError('탐지 기록이 없습니다. 삭제되었거나 번호가 잘못되었습니다.');
        } else if (error.status === 401) {
            showError('로그인 상태를 확인해주세요.');
        } else if (error.status === 403) {
            showError('탐지 정보를 조회할 권한이 없습니다.');
        } else {
            showError(error.message || '탐지 정보를 불러오는 중 오류가 발생했습니다.');
        }
        return;
    }

    // 삭제 버튼 (MASTER가 아니면 HTML에 버튼이 없으므로 ?.로 건너뜀)
    deleteButton?.addEventListener('click', async () => {
        const ok = window.confirm(
            `탐지 번호 ${dlNo} 기록을 삭제할까요?\n삭제한 기록은 복구할 수 없습니다.`
        );

        if (!ok) {
            return;
        }

        deleteButton.disabled = true;

        try {
            await fetchJson(
                `/detections/delete?dl_no=${encodeURIComponent(dlNo)}`,
                { method: 'DELETE' }
            );

            // 삭제 후 목록으로 이동
            window.location.href = '/dashboard/detection';

        } catch (error) {
            console.error(error);
            deleteButton.disabled = false;

            window.alert(error.status === 403
                ? '삭제 권한이 없습니다.'
                : error.message);
        }
    });
});