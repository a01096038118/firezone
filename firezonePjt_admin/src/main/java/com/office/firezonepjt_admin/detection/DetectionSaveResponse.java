package com.office.firezonepjt_admin.detection;

public record DetectionSaveResponse(
        int dl_no,          // 탐지 기록 번호
        String result       // CREATED(신규 저장) / UPDATED( 기존 기록 갱신)
) {
    public static final String CREATED = "CREATED";
    public static final String UPDATED = "UPDATED";

    public static DetectionSaveResponse created(int dlNo) {
        return new DetectionSaveResponse(dlNo, CREATED);
    }

    public static DetectionSaveResponse updated(int dlNo) {
        return new DetectionSaveResponse(dlNo, UPDATED);
    }
}
