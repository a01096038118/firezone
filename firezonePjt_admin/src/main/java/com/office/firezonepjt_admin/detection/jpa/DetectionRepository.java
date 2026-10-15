package com.office.firezonepjt_admin.detection.jpa;


import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import java.util.Optional;

public interface DetectionRepository extends JpaRepository<DetectionEntity, Integer>,
                                            JpaSpecificationExecutor<DetectionEntity> {

    Optional<DetectionEntity>
    findFirstByDlCameraIdAndDlZoneNoAndDlCarNumberAndDlViolationTypeOrderByDlLastDetectedAtDesc(
            String cameraId,
            String zoneNo,
            String carNumber,
            String violationType
    );
}
