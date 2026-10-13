package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.DetectionEntity;
import com.office.firezonepjt_admin.detection.jpa.DetectionRepository;
import com.office.firezonepjt_admin.detection.jpa.SystemLogEntity;
import com.office.firezonepjt_admin.detection.jpa.SystemLogRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

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

        // Dto에 담긴 데이터를 Entity에 옮김
        DetectionEntity entity = dto.toEntity();

        // detection_log 테이블에 저장
        DetectionEntity saved = detectionRepository.save(entity);

        return saved.getDlNo();

    }

    // 로그 기록 저장
    public Integer saveSystemLog(SystemLogDto dto) {

        // Dto에 담긴 log데이터를 Entity에 옮김
        SystemLogEntity entity = dto.logEntity();

        // system_log 테이블에 저장
        SystemLogEntity saved = systemLogRepository.save(entity);

        return saved.getSlNo();
    }

    // 탐지 목록 조회
    public List<DetectionDto> getDetectionList() {
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
}
