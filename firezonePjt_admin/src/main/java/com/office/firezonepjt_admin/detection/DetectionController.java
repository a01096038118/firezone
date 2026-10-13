package com.office.firezonepjt_admin.detection;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@Controller
@ResponseBody
@RequestMapping("/detections")
public class DetectionController {

    final DetectionService detectionService;

    public DetectionController(DetectionService detectionService) {
        this.detectionService = detectionService;
    }

    // 탐지 기록 저장
    @PostMapping
    public Integer saveDetection(@RequestBody DetectionDto dto) {
        log.info("saveDetection()");

        return detectionService.saveDetection(dto);
    }

    // 로그 기록 저장
    @PostMapping("/log")
    public Integer saveSystemLog(@RequestBody SystemLogDto dto) {
        log.info("saveSystemLog()");

        return detectionService.saveSystemLog(dto);
    }


    // 탐지 목록 조회
    @GetMapping("/list")
    public List<DetectionDto> getDetectionList() {
        log.info("getDetectionList()");

        return detectionService.getDetectionList();
    }


    // 탐지 목록 상세 조회
    @GetMapping("/detail")
    public DetectionDto getDetectionDetail(
            @RequestParam("dl_no") Integer dl_no) {
        log.info("getDetectionDetail()");

        return detectionService.getDetectionDetail(dl_no);
    }

    // 로그 목록 조회
    @GetMapping("/log_list")
    public List<SystemLogDto> getSystemLog() {
        log.info("getSystemLog()");

        return detectionService.getSystemLog();
    }

    // 로그 목록 상세 조회
    @GetMapping("/log_detail")
    public SystemLogDto getSystemLogDetail(
            @RequestParam("sl_no") Integer sl_no) {
        log.info("getSystemLogDetail()");

        return detectionService.getSystemLogDetail(sl_no);
    }


    // 탐지 기록 삭제
    @DeleteMapping("/delete")
    public void deleteDetection(
            @RequestParam("dl_no") Integer dl_no) {
        log.info("deleteDetection()");

        detectionService.deleteDetection(dl_no);
    }

    // CSV 다운로드
    @GetMapping("/csv")
    public ResponseEntity<byte[]> downloadDetectionCsv() {
        log.info("downloadDetectionCsv()");

        byte[] csv = detectionService.downloadDetectionCsv();

        return ResponseEntity.ok()
                // 다운로드 응답 처리
                .header(
                        HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"detections.csv\""
                )
                .contentType(
                        MediaType.parseMediaType("text/csv;charset=UTF-8")
                )
                .body(csv);
    }


}
