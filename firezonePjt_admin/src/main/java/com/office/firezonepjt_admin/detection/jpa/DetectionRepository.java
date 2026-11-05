package com.office.firezonepjt_admin.detection.jpa;


import jakarta.validation.constraints.NotBlank;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.Optional;

public interface DetectionRepository extends JpaRepository<DetectionEntity, Integer>,
                                            JpaSpecificationExecutor<DetectionEntity> {


    Optional<DetectionEntity>
    findFirstByDlCameraIdAndDlZoneNoAndDlCarNumberAndDlTypeOrderByDlLastTimeDesc(
            String dlCameraId,
            String dlZoneNo,
            String carNumber,
            String dlViolationType
    );
}
