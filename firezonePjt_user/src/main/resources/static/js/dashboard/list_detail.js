document.addEventListener('DOMContentLoaded', async () => {

    // 상세 화면 주소에서 탐지 번호 가져오기
    // 예: /dashboard/detail?dl_no=5
    const params = new URLSearchParams(window.location.search);
    const dlNo = params.get('dl_no');

    if (!dlNo) {
        alert('탐지 번호가 없습니다.');
        return;
    }

    try {
        // Controller에 상세 정보 요청
        const response = await fetch(
            `/detections/detail?dl_no=${encodeURIComponent(dlNo)}`
        );

        if (!response.ok) {
            throw new Error('탐지 정보를 불러오지 못했습니다.');
        }

        // 응답받은 JSON을 자바스크립트 객체로 변환
        const dto = await response.json();

        // HTML의 각 위치에 데이터 표시
        document.getElementById('detection_no').textContent =
            dto.dl_no ?? '-';

        document.getElementById('camera_id').textContent =
            dto.dl_camera_id ?? '-';

        document.getElementById('zone_id').textContent =
            dto.dl_zone_no ?? '-';

        document.getElementById('violation_type').textContent =
            dto.dl_violation_type ?? '-';

        document.getElementById('car_number').textContent =
            dto.dl_car_number ?? '-';

        document.getElementById('first_detected').textContent =
            dto.dl_first_detected_at?.replace('T', ' ') ?? '-';

        document.getElementById('last_detected').textContent =
            dto.dl_last_detected_at?.replace('T', ' ') ?? '-';


        // 이미지 주소가 있으면 사진 표시
        if (dto.dl_image_path) {
            const img = document.getElementById('detection_img');
            img.src = dto.dl_image_path;
            img.hidden = false;
        }

    } catch (error) {
        console.error(error);
        alert('탐지 정보를 불러오는 중 오류가 발생했습니다.');
    }
});