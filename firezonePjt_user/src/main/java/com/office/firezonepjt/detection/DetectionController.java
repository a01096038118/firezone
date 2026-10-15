package com.office.firezonepjt.detection;


import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDate;

@Slf4j
@Controller
@ResponseBody
@RequestMapping("/detections")
public class DetectionController {

    final private DetectionService detectionService;

    public DetectionController(DetectionService detectionService) {
        this.detectionService = detectionService;
    }


    // 탐지 목록 조회
    @GetMapping("/list")
    public DetectionPageDto  getDetectionList(
            // 카메라 ID 검색
            @RequestParam(name = "cameraId", required = false)
            String cameraId,
            // zone(구역번호 조회)
            @RequestParam(name = "zoneNo", required = false)
            String zoneNo,
            // 조회 시작일 (yyyy-MM-dd, 최초 탐지 날짜 기준)
            @RequestParam(name = "from", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate from,
            // 조회 종료일 (yyyy-MM-dd, 해당 날짜 포함)
            @RequestParam(name = "to", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate to,
            // 페이지 번호
            @RequestParam(name = "page", defaultValue = "1")
            int page,
            // 페이지 기록 수
            @RequestParam(name = "size", defaultValue = "10")
            int size,
            // 탐지 번호 정렬
            @RequestParam(name = "direction", defaultValue = "desc")
            String direction
    ) {
        log.info("getDetectionList()");

        return detectionService.getDetectionList(
                cameraId,
                zoneNo,
                from,
                to,
                page,
                size,
                direction
        );
    }


    // 탐지 목록 상세 조회
    @GetMapping("/detail")
    public DetectionDto getDetectionDetail(
            @RequestParam("dl_no") Integer dl_no) {
        log.info("getDetectionDetail()");

        return detectionService.getDetectionDetail(dl_no);
    }



}
