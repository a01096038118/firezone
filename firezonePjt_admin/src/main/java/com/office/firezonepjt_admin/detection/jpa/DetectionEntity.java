package com.office.firezonepjt_admin.detection.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Entity
@Builder
@Table(name = "detection_log")
@AllArgsConstructor
@NoArgsConstructor
public class DetectionEntity {

    @Id
    @Column(name = "dl_no")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int dlNo;                   // 탐지 기록 번호

    @Column(name = "dl_camera_id", nullable = false, length = 20)
    private String dlCameraId;          // 감지 카메라 ID

    @Column(name = "dl_zone_no", nullable = false, length = 20)
    private String dlZoneNo;            // 탐지 구역번호

    @Column(name = "dl_violation_type", nullable = false, length = 30)
    private String dlType;              // 위반 유형

    @Column(name = "dl_car_number", nullable = false, length = 20)
    private String dlCarNumber;         // 인식 차량 번호

    @Column(name = "dl_image_path", nullable = false, length = 255)
    private String dlImage;             // 탐지 이미지 경로

    @Column(name = "dl_first_detected_at", nullable = false)
    private LocalDateTime dlFirstTime;  // 최초 탐지 시간

    @Column(name = "dl_last_detected_at", nullable = false)
    private LocalDateTime dlLastTime;   // 마지막 탐지 시간

}
