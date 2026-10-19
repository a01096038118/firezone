package com.office.firezonepjt_admin.detection;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/detections")
public class DetectionController {

    final private DetectionService detectionService;

    // 탐지 저장을 허용할 IP 목록
    private final Set<String> allowedIps;

    public DetectionController(
            DetectionService detectionService,
            @Value("${detection.allowed-ips:}") String allowedIps) {
        this.detectionService = detectionService;
        this.allowedIps = Arrays.stream(allowedIps.split(","))
                .map(String::trim)
                .filter(ip -> !ip.isEmpty())
                .collect(Collectors.toSet());
    }


    // 탐지 기록 저장 (허용된 IP의 Flask 서버만 가능)
    @PostMapping
    public ResponseEntity<DetectionSaveResponse> saveDetection(
            HttpServletRequest request,
            @Valid @RequestBody DetectionDto dto) {
        log.info("saveDetection()");

        checkAllowedIp(request);

        DetectionSaveResponse response = detectionService.saveDetection(dto);

        HttpStatus status = DetectionSaveResponse.CREATED.equals(response.result())
                ? HttpStatus.CREATED
                : HttpStatus.OK;

        return ResponseEntity.status(status).body(response);
    }

    // 요청을 보낸 서버의 IP 확인
    private void checkAllowedIp(HttpServletRequest request) {
        String remoteIp = request.getRemoteAddr();

        if (!allowedIps.contains(remoteIp)) {
            log.warn("허용되지 않은 IP의 탐지 저장 요청: {}", remoteIp);

            throw new ResponseStatusException(
                    HttpStatus.FORBIDDEN, "허용되지 않은 요청입니다.");
        }
    }

    // 탐지 목록 조회
    @GetMapping("/list")
    public DetectionPageDto getDetectionList(
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
