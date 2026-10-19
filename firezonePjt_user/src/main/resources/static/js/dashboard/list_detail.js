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

        // 이미지 주소가 있으면 Flask 주소를 붙여 사진 표시
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