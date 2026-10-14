package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.DetectionEntity;
import com.office.firezonepjt_admin.detection.jpa.DetectionRepository;
import jakarta.validation.constraints.NotNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class DetectionService {
    private final DetectionRepository detectionRepository;
    private static final DateTimeFormatter LOG_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");


    public DetectionService(DetectionRepository detectionRepository
                            ) {
        this.detectionRepository = detectionRepository;
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


    // 탐지 목록 조회
    public List<DetectionDto> getDetectionList(String cameraId, String zoneNo, int page, int size, String direction) {
        log.info("getDetectionList()");

        // 최신 데이터 순서로 조회
        List<DetectionEntity> entities =
                detectionRepository.findAll(
                        Sort.by(Sort.Direction.DESC, "dlNo"));


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



    // 탐지 기록 삭제
    @Transactional
    public void deleteDetection(Integer dlNo) {
        log.info("deleteDetection()");

        DetectionEntity entity = findDetection(dlNo);

        detectionRepository.delete(entity);
    }

    // CSV 셀 값 변환
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

        List<DetectionEntity> entities =
                detectionRepository.findAll(Sort.by(Sort.Direction.DESC, "dlNo"));

        List<DetectionDto> detections = toDtoList(entities);

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
            csv.append(csvCell(csvTime(dto.getDl_first_detected_at()))).append(",");
            csv.append(csvCell(csvTime(dto.getDl_last_detected_at())));
            csv.append("\r\n");
        }
        return csv.toString().getBytes(StandardCharsets.UTF_8);
    }

    private String csvTime(LocalDateTime time) {
        return time == null ? "" : time.format(LOG_FMT);
    }

    private List<DetectionDto> toDtoList(List<DetectionEntity> entities) {

        List<DetectionDto> dtoList = new ArrayList<>();

        for(DetectionEntity entity : entities) {
            dtoList.add(DetectionDto.fromEntity(entity));
        }
        return dtoList;
    }


}
