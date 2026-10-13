package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.DetectionEntity;
import com.office.firezonepjt_admin.detection.jpa.DetectionRepository;
import com.office.firezonepjt_admin.detection.jpa.SystemLogEntity;
import com.office.firezonepjt_admin.detection.jpa.SystemLogRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class DetectionService {
    private final DetectionRepository detectionRepository;
    private final SystemLogRepository systemLogRepository;


    public DetectionService(DetectionRepository detectionRepository,
                            SystemLogRepository systemLogRepository
                            ) {
        this.detectionRepository = detectionRepository;
        this.systemLogRepository = systemLogRepository;
    }


    // 탐지 기록 저장
    public Integer saveDetection(DetectionDto dto) {
        log.info("saveDetection()");

        // Dto에 담긴 데이터를 Entity에 옮김
        DetectionEntity entity = dto.toEntity();

        // detection_log 테이블에 저장
        DetectionEntity saved = detectionRepository.save(entity);

        return saved.getDlNo();

    }


    // 로그 기록 저장
    public Integer saveSystemLog(SystemLogDto dto) {
        log.info("saveSystemLog()");

        // Dto에 담긴 log데이터를 Entity에 옮김
        SystemLogEntity entity = dto.logEntity();

        // system_log 테이블에 저장
        SystemLogEntity saved = systemLogRepository.save(entity);

        return saved.getSlNo();
    }


    // 탐지 목록 조회
    public List<DetectionDto> getDetectionList() {
        log.info("getDetectionList()");

        // 최신 데이터 순서로 조회
        List<DetectionEntity> entities =
                detectionRepository.findAll(
                        Sort.by(Sort.Direction.DESC, "dl_no")
                );

        // Entity 목록을 Dto 목록으로 변환
        List<DetectionDto> dtoList = new ArrayList<>();

        for (DetectionEntity entity : entities) {
            dtoList.add(DetectionDto.fromEntity(entity));

        }
        return dtoList;
    }


    // 탐지 목록 상세 조회
    public DetectionDto getDetectionDetail(Integer dlNo) {
        log.info("getDetectionDetail()");

        DetectionEntity entity = findDetection(dlNo);

        return DetectionDto.fromEntity(entity);
    }

    private DetectionEntity findDetection(Integer dlNo) {

        return detectionRepository.findById(dlNo)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "탐지 기록이 없습니다."
                ));
    }


    // 로그 목록 조회
    public List<SystemLogDto> getSystemLog() {
        log.info("getSystemLog()");

        // 최신 데이터 순서로 조회
        List<SystemLogEntity> entities =
                systemLogRepository.findAll(
                        Sort.by(Sort.Direction.DESC, "sl_no")
                );

        // Entity 목록을 Dto 목록으로 변환
        List<SystemLogDto> dtoList = new ArrayList<>();

        for (SystemLogEntity entity : entities) {
            dtoList.add(SystemLogDto.fromLogEntity(entity));

        }
        return dtoList;

    }


    // 로그 목록 상세 조회
    public SystemLogDto getSystemLogDetail(Integer slNo) {
        log.info("getSystemLogDetail()");

        SystemLogEntity entity = findSystemLog(slNo);

        return SystemLogDto.fromLogEntity(entity);
    }

    private SystemLogEntity findSystemLog(Integer slNo) {

        return systemLogRepository.findById(slNo)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "탐지 기록이 없습니다."
                ));

    }


    // 탐지 기록 삭제
    @Transactional
    public void deleteDetection(Integer dlNo) {
        log.info("deleteDetection()");

        DetectionEntity entity = findDetection(dlNo);

        detectionRepository.delete(entity);
    }


    private String csvCell(Object value) {
        // 값이 없으면 빈칸으로 처리
        if (value == null) {
            return "";
        }

        // 숫자, 날짜 등을 문자열로 변환
        String text = value.toString();

        // Excel이 텍스트를 수식으로 실행하지 않도록 처리
        if (text.stripLeading().matches("^[=+@-].*")) {
            text = "'" + text;
        }

        // 큰따옴표를 두 개로 바꾸고 값을 큰따옴표로 감싸기
        return "\"" + text.replace("\"", "\"\"") + "\"";
    }


    // CSV 생성 및 다운로드
    public byte[] downloadDetectionCsv() {
        log.info("downloadDetectionCsv()");

        List<DetectionDto> detections = getDetectionList();

        StringBuilder csv = new StringBuilder();

        // Excel에서 UTF-8 한글 인식
        csv.append('\uFEFF');

        // CSV 첫 줄: 열 제목
        csv.append(
                "탐지 번호, 카메라 ID, 구역번호, 위반유형,"
                + "차량번호, 이미지 경로, 최초 탐지 시간, 마지막 탐지 시간\r\n"
        );

        // 탐지 기록 한 건마다 추가
        for (DetectionDto dto : detections) {
            csv.append(csvCell(dto.getDl_no())).append(",");
            csv.append(csvCell(dto.getDl_camera_id())).append(",");
            csv.append(csvCell(dto.getDl_zone_no())).append(",");
            csv.append(csvCell(dto.getDl_violation_type())).append(",");
            csv.append(csvCell(dto.getDl_car_number())).append(",");
            csv.append(csvCell(dto.getDl_image_path())).append(",");
            csv.append(csvCell(dto.getDl_first_detected_at())).append(",");
            csv.append(csvCell(dto.getDl_last_detected_at()));
            csv.append("\r\n");
        }
        return csv.toString().getBytes(StandardCharsets.UTF_8);
    }





}
