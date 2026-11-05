document.addEventListener('DOMContentLoaded', () => {

    const PAGE_SIZE = 20;       // 한 페이지에 보여줄 기록 수
    // 탐지 삭제 권한(MASTER) 여부: HTML의 can_delete meta 태그가 있을 때만 true
    const canDelete = document.querySelector('meta[name="can_delete"]') !== null;
    const COLUMN_COUNT = canDelete ? 8 : 7;     // 표의 열 개수 (삭제 열은 MASTER만)

    const listBody = document.querySelector('#detection_log_list');
    const listNotice = document.querySelector('#list_notice');
    const totalCount = document.querySelector('#total_count');
    const pageInfo = document.querySelector('#page_info');
    const prevButton = document.querySelector('#prev_page');
    const nextButton = document.querySelector('#next_page');

    const searchForm = document.querySelector('#search_form');
    const cameraInput = document.querySelector('#search_camera_id');
    const zoneInput = document.querySelector('#search_zone_no');
    const fromInput = document.querySelector('#search_from');
    const toInput = document.querySelector('#search_to');
    const resetButton = document.querySelector('#search_reset');

    // 현재 페이지 상태
    let currentPage = 1;
    let totalPages = 1;

    // '조회' 버튼으로 확정한 검색 조건
    // (입력창만 고치고 페이지를 넘길 때 조건이 바뀌지 않게 따로 보관)
    let appliedFilter = { cameraId: '', zoneNo: '', from: '', to: '' };


    // 안내 문구 표시 / 숨김
    function showNotice(message) {
        listNotice.textContent = message;
        listNotice.hidden = false;
    }

    function hideNotice() {
        listNotice.textContent = '';
        listNotice.hidden = true;
    }

    // 로딩·빈 목록·오류 메시지를 표 안에 표시
    function showMessage(message) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');

        cell.colSpan = COLUMN_COUNT;
        cell.textContent = message;

        row.appendChild(cell);
        listBody.replaceChildren(row);
    }

    // 페이지 이동 버튼 상태 갱신
    function updatePaging() {
        pageInfo.textContent = `${currentPage} / ${totalPages}`;
        prevButton.disabled = currentPage <= 1;
        nextButton.disabled = currentPage >= totalPages;
    }

    // 현재 검색 조건이 있는지
    function hasFilter() {
        return Object.values(appliedFilter).some(value => value !== '');
    }

    // 목록 조회 주소 만들기
    function buildListUrl(page) {
        const params = new URLSearchParams({
            page: String(page),
            size: String(PAGE_SIZE),
            direction: 'desc'
        });

        if (appliedFilter.cameraId) params.set('cameraId', appliedFilter.cameraId);
        if (appliedFilter.zoneNo) params.set('zoneNo', appliedFilter.zoneNo);
        if (appliedFilter.from) params.set('from', appliedFilter.from);
        if (appliedFilter.to) params.set('to', appliedFilter.to);

        return `/detections/list?${params.toString()}`;
    }

    // 조회한 목록을 표에 표시
    // 화면에 보여줄 순번 (DB의 탐지 번호와 별개)
    // 최신순(desc)이라 전체 건수에서 거꾸로 셈 → 삭제하면 다시 조회할 때 빈 번호 없이 이어짐
    function rowNumber(data, index) {
        return data.totalElements - (data.page - 1) * data.size - index;
    }

    function showDetections(data) {
        listBody.replaceChildren();

        data.content.forEach((dto, index) => {
            const row = document.createElement('tr');

            // 순번 (줄 전체를 누르면 상세 화면으로 이동, 이동은 실제 탐지 번호 dl_no 사용)
            const noCell = document.createElement('td');
            noCell.textContent = String(rowNumber(data, index));
            row.appendChild(noCell);

            // 나머지 여섯 개의 열
            const values = [
                displayValue(dto.dl_camera_id),
                displayValue(dto.dl_zone_no),
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

            // 삭제 버튼 (MASTER만)
            if (canDelete) {
                const deleteCell = document.createElement('td');
                const deleteButton = document.createElement('button');

                deleteButton.type = 'button';
                deleteButton.textContent = '삭제';
                deleteButton.addEventListener('click', (event) => {
                    event.stopPropagation();    // 삭제 버튼을 눌러도 상세 화면으로 이동하지 않게
                    deleteDetection(dto.dl_no, deleteButton);
                });

                deleteCell.appendChild(deleteButton);
                row.appendChild(deleteCell);
            }

            makeDetailRow(row, dto.dl_no);
            listBody.appendChild(row);
        });
    }

    // 서버에서 탐지 목록 조회
    async function fetchDetectionList(page) {
        showMessage('탐지 기록을 불러오는 중입니다.');
        prevButton.disabled = true;
        nextButton.disabled = true;

        try {
            const data = await fetchJson(buildListUrl(page));

            if (!data || !Array.isArray(data.content)) {
                throw new ApiError('탐지 목록 응답 형식이 올바르지 않습니다.', 0);
            }

            currentPage = data.page;
            totalPages = Math.max(data.totalPages, 1);
            totalCount.textContent = `총 ${data.totalElements}건`;

            // 삭제 등으로 현재 페이지가 없어졌으면 마지막 페이지를 다시 조회
            if (data.content.length === 0
                && data.totalElements > 0
                && page > totalPages) {
                await fetchDetectionList(totalPages);
                return;
            }

            if (data.content.length === 0) {
                showMessage(hasFilter()
                    ? '조건에 맞는 탐지 기록이 없습니다.'
                    : '저장된 탐지 기록이 없습니다.');
            } else {
                showDetections(data);
            }

            updatePaging();

        } catch (error) {
            console.error('탐지 목록 조회 오류:', error);
            totalCount.textContent = '';
            showMessage(error.message);
            updatePaging();
            prevButton.disabled = true;
            nextButton.disabled = true;
        }
    }

    // 탐지 기록 삭제
    async function deleteDetection(dlNo, button) {
        const ok = window.confirm(
            `탐지 번호 ${dlNo} 기록을 삭제할까요?\n삭제한 기록은 복구할 수 없습니다.`
        );

        if (!ok) {
            return;
        }

        button.disabled = true;

        try {
            await fetchJson(
                `/detections/delete?dl_no=${encodeURIComponent(dlNo)}`,
                { method: 'DELETE' }
            );

            await fetchDetectionList(currentPage);
            showNotice('탐지 기록을 삭제했습니다.');

        } catch (error) {
            console.error('탐지 기록 삭제 오류:', error);
            button.disabled = false;

            showNotice(error.status === 403
                ? '삭제 권한이 없습니다.'
                : error.message);
        }
    }

    // '조회' 버튼
    searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        hideNotice();

        const from = fromInput.value;
        const to = toInput.value;

        // 날짜는 yyyy-MM-dd 문자열이라 그대로 비교해도 됨
        if (from && to && from > to) {
            showNotice('시작일이 종료일보다 늦을 수 없습니다.');
            return;
        }

        appliedFilter = {
            cameraId: cameraInput.value.trim(),
            zoneNo: zoneInput.value.trim(),
            from: from,
            to: to
        };

        fetchDetectionList(1);
    });

    // '초기화' 버튼
    resetButton.addEventListener('click', () => {
        searchForm.reset();
        hideNotice();

        appliedFilter = { cameraId: '', zoneNo: '', from: '', to: '' };

        fetchDetectionList(1);
    });

    // 페이지 이동
    prevButton.addEventListener('click', () => {
        hideNotice();
        fetchDetectionList(currentPage - 1);
    });

    nextButton.addEventListener('click', () => {
        hideNotice();
        fetchDetectionList(currentPage + 1);
    });

    fetchDetectionList(1);
});