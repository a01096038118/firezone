package com.office.firezonepjt_admin.detection.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface DetectionRepository extends JpaRepository<DetectionEntity, Integer>,
                                            JpaSpecificationExecutor<DetectionEntity> {
}
