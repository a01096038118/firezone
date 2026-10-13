package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.SystemLogEntity;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@Controller
@RequestMapping("/detections")
public class DetectionController {

    final DetectionService detectionService;

    public DetectionController(DetectionService detectionService) {
        this.detectionService = detectionService;
    }

    // 탐지 기록 저장
    @PostMapping
    public Integer saveDetection(@RequestBody DetectionDto dto) {
        return detectionService.saveDetection(dto);
    }

    // 로그 기록 저장
    @PostMapping
    public Integer saveSystemLog(@RequestBody SystemLogDto dto) {
        return detectionService.saveSystemLog(dto);
    }


    // 탐지 목록 조회
    @GetMapping("/list")
    public List<DetectionDto> getDetectionList() {
        return detectionService.getDetectionList();
    }

    // 탐지 목록 상세 조회
    @GetMapping("/detail")
    public DetectionDto getDetectionDetail(
            @RequestParam("dl_no") Integer dl_no) {

        return detectionService.getDetectionDetail(dl_no);
    }

    // 탐지 기록 삭제
    @DeleteMapping
    public void deleteDetection(
            @RequestParam("dl_no") Integer dl_no) {

        detectionService.deleteDetection(dl_no);
    }

    @GetMapping("/csv")
    public ResponseEntity<byte[]> downloadDetectionCsv() {

        byte[] csv = detectionService.downloadDetectionCsv();

        return ResponseEntity.ok()
                // 다운로드 응답 처리
                .header(
                        HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"detextions.csv\""
                )
                .contentType(
                        MediaType.parseMediaType("text/csv;charset=UTF-8")
                )
                .body(csv);
    }


}
