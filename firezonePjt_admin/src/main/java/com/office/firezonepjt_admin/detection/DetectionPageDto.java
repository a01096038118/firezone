package com.office.firezonepjt_admin.detection;


import java.util.List;


public record DetectionPageDto(
        List<DetectionDto> content,     // 현재 페이지 기록 목록
        long totalElements,             // 조건에 맞는 전체 기록 수
        int totalPages,                 // 전체 페이지 수
        int page,                       // 현재 페이지 번호
        int size                        // 페이지당 기록 수
) {
}
