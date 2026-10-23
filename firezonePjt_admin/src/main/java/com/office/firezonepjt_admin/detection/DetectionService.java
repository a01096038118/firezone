package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.DetectionEntity;
import com.office.firezonepjt_admin.detection.jpa.DetectionRepository;
import jakarta.persistence.criteria.Predicate;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
public class DetectionService {
    private final DetectionRepository detectionRepository;
    private static final DateTimeFormatter LOG_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private final long sameEventSeconds;
    private static final int MAX_PAGE_SIZE = 100;

    public DetectionService(
            DetectionRepository detectionRepository,
            @Value("${detection.same-event-seconds:30}") long sameEventSeconds) {
        this.detectionRepository = detectionRepository;
        this.sameEventSeconds = sameEventSeconds;
    }


    // 탐지 기록 저장
    @Transactional
    public DetectionSaveResponse saveDetection(DetectionDto dto) {
        log.info("saveDetection()");

        // Flask가 보낸 최초·마지막 탐지 시간
        LocalDateTime firstAt = dto.getDl_first_detected_at();
        LocalDateTime lastAt = dto.getDl_last_detected_at();

        if (firstAt == null || lastAt == null) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "탐지 시간이 필요합니다."
            );
        }

        if (firstAt.isAfter(lastAt)) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "최초 탐지 시간이 마지막 탐지 시간보다 늦을 수 없습니다."
            );
        }

        String carNumber = dto.getDl_car_number();

        // 차량번호가 있어야 같은 차량인지 비교할 수 있음
        if (carNumber == null || carNumber.isBlank()) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "차량번호가 필요합니다."
            );
        }

        Optional<DetectionEntity> result =
                detectionRepository
                        .findFirstByDlCameraIdAndDlZoneNoAndDlCarNumberAndDlTypeOrderByDlLastTimeDesc(
                                dto.getDl_camera_id(),
                                dto.getDl_zone_no(),
                                carNumber,
                                dto.getDl_violation_type()
                        );

            if (result.isPresent()) {

                DetectionEntity entity = result.get();

                // 기존 '마지막' 탐지시간
                LocalDateTime lastTime = entity.getDlLastTime();

                // 기존 마지막 탐지 시간과 설정된 시간(초) 이내이고, 같은 날짜일 때만 같은 기록으로 판단
                // (자정을 넘기면 계속 서 있던 차량이라도 다음 날짜의 새 기록으로 저장)
                if (lastTime != null
                        && lastTime.toLocalDate().equals(lastAt.toLocalDate())
                        && !lastAt.isBefore(lastTime.minusSeconds(sameEventSeconds))
                        && !lastAt.isAfter(lastTime.plusSeconds(sameEventSeconds))) {

                    // 새로운 시간이 더 최근일 때만 수정
                    if (lastAt.isAfter(lastTime)) {
                        entity.setDlLastTime(lastAt);
                    }

                    return DetectionSaveResponse.updated(entity.getDlNo());
                }
            }

        // 최초 탐지 시간이 전날이면 마지막 탐지 날짜의 00:00으로 맞춤
        // (자정을 넘겨 새로 만드는 기록이 다음 날짜로 조회되도록)
        if (firstAt.toLocalDate().isBefore(lastAt.toLocalDate())) {
            dto.setDl_first_detected_at(lastAt.toLocalDate().atStartOfDay());
        }

        // detection_log 테이블에 저장
        DetectionEntity saved = detectionRepository.save(dto.toEntity());

        return DetectionSaveResponse.created(saved.getDlNo());

    }


    // 탐지 목록 조회
    @Transactional(readOnly = true)
    public DetectionPageDto getDetectionList(
            String cameraId, String zoneNo,
            LocalDate from, LocalDate to,
            int page, int size, String direction
            ) {

        log.info("getDetectionList()");

        if (from != null && to != null && from.isAfter(to)) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "조회 시작일이 종료일보다 늦을 수 없습니다."
            );
        }

        // 페이지 번호는 1부터 JPA는 0부터 시작
        int pageIndex = Math.max(page -1, 0);
        int pageSize = Math.min(Math.max(size, 1), MAX_PAGE_SIZE);

        // 탐지 번호 기준 정렬 (desc가 아니면 asc)
        Sort.Direction sortDirection =
                "asc".equalsIgnoreCase(direction) ? Sort.Direction.ASC : Sort.Direction.DESC;

        Pageable pageable = PageRequest.of(pageIndex, pageSize, Sort.by(sortDirection, "dlNo"));

        // 조건이 있는 것만 where 절에 추가
        Specification<DetectionEntity> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (cameraId != null && !cameraId.isBlank()) {
                predicates.add(cb.equal(root.get("dlCameraId"), cameraId));
            }

            if (zoneNo != null && !zoneNo.isBlank()) {
                predicates.add(cb.equal(root.get("dlZoneNo"), zoneNo));
            }

            // 기간은 최초 탐지 시간 기준 (from 00:00 이상, to 다음날 00:00 미만)
            if (from != null) {
                predicates.add(cb.greaterThanOrEqualTo(
                        root.get("dlFirstTime"), from.atStartOfDay()));
            }

            if (to != null) {
                predicates.add(cb.lessThan(
                        root.get("dlFirstTime"), to.plusDays(1).atStartOfDay()));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<DetectionEntity> result = detectionRepository.findAll(spec, pageable);

        // Entity 목록을 Dto 목록으로 변환
        List<DetectionDto> content = toDtoList(result.getContent());

        return new DetectionPageDto(
                content,
                result.getTotalElements(),
                result.getTotalPages(),
                pageIndex + 1,
                pageSize
        );
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
        String trimmed = text.stripLeading();
        if (!text.isEmpty()
                && ("\t\r\n".indexOf(text.charAt(0)) >= 0
                || (!trimmed.isEmpty() && "=+-@".indexOf(trimmed.charAt(0)) >= 0))) {
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
        csv.append("탐지 번호,카메라 ID,구역번호,위반유형,")
                .append("차량번호,이미지 경로,최초 탐지 시간,마지막 탐지 시간\r\n"
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
