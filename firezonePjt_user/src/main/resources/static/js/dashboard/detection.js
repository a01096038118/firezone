document.addEventListener('DOMContentLoaded', () => {

    const PAGE_SIZE = 20;       // 한 페이지에 보여줄 기록 수

    const listBody = document.querySelector('#detection_log_list');
    const prevButton = document.querySelector('#prev_page');
    const nextButton = document.querySelector('#next_page');
    const pageInfo = document.querySelector('#page_info');

    let currentPage = 1;
    let totalPages = 1;

    // 로딩·빈 목록·오류 메시지 표시
    function showMessage(message) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');

        cell.colSpan = 5;
        cell.textContent = message;

        row.appendChild(cell);
        listBody.replaceChildren(row);
    }

    // 페이지 이동 버튼 상태 갱신
    function updatePager() {
        pageInfo.textContent = `${currentPage} / ${totalPages}`;
        prevButton.disabled = currentPage <= 1;
        nextButton.disabled = currentPage >= totalPages;
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
    async function fetchDetectionList(page) {
        showMessage('탐지 기록을 불러오는 중입니다.');

        try {
            const data = await fetchJson(
                `/detections/list?page=${page}&size=${PAGE_SIZE}&direction=desc`
            );

            // 서버 응답: { content: [...], totalElements, totalPages, page, size }
            if (!data || !Array.isArray(data.content)) {
                throw new ApiError('탐지 목록 응답 형식이 올바르지 않습니다.', 0);
            }

            // 기록이 삭제되어 현재 페이지가 없어진 경우 마지막 페이지로 이동
            if (data.content.length === 0
                && page > 1
                && data.totalPages > 0
                && page > data.totalPages) {
                fetchDetectionList(data.totalPages);
                return;
            }

            currentPage = data.page;
            totalPages = Math.max(data.totalPages, 1);
            updatePager();

            if (data.content.length === 0) {
                showMessage('저장된 탐지 기록이 없습니다.');
                return;
            }

            showDetections(data.content);

        } catch (error) {
            console.error('탐지 목록 조회 오류:', error);
            showMessage(error.message);

            if (error.status === 401) {
                window.location.href = LOGIN_URL;
            }
        }
    }

    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            fetchDetectionList(currentPage - 1);
        }
    });

    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            fetchDetectionList(currentPage + 1);
        }
    });

    updatePager();
    fetchDetectionList(1);
});