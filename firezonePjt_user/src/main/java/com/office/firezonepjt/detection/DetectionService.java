package com.office.firezonepjt.detection;

import com.office.firezonepjt.detection.jpa.DetectionEntity;
import com.office.firezonepjt.detection.jpa.DetectionRepository;
import jakarta.persistence.criteria.Predicate;
import lombok.extern.slf4j.Slf4j;
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



@Slf4j
@Service
public class DetectionService {
    private final DetectionRepository detectionRepository;
    private static final DateTimeFormatter LOG_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final int MAX_PAGE_SIZE = 100;

    public DetectionService(DetectionRepository detectionRepository) {
        this.detectionRepository = detectionRepository;
    }


    // 탐지 목록 조회
    @Transactional(readOnly = true)
    public DetectionPageDto getDetectionList(
                                        String cameraId, String zoneNo,
                                        LocalDate from, LocalDate to,
                                        int page, int size, String direction) {

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
        List<DetectionDto> content = new ArrayList<>();
        for (DetectionEntity entity : result.getContent()) {
            content.add(DetectionDto.fromEntity(entity));
        }

        return new DetectionPageDto(
                content,
                result.getTotalElements(),
                result.getTotalPages(),
                pageIndex + 1,
                pageSize
        );
    }


    // 탐지 목록 상세 조회
    @Transactional(readOnly = true)
    public DetectionDto getDetectionDetail(Integer dlNo) {
        log.info("getDetectionDetail()");

        DetectionEntity entity = detectionRepository.findById(dlNo)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "탐지 기록이 없습니다."
                ));

        return DetectionDto.fromEntity(entity);
    }


}
