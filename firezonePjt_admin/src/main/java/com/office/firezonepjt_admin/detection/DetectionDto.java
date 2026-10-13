package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.DetectionEntity;
import com.office.firezonepjt_admin.detection.jpa.SystemLogEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.cglib.core.Local;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class DetectionDto {

    private int dl_no;                              // 탐지 기록 번호
    private String dl_camera_id;                    // 감지 카메라 ID
    private String dl_zone_no;                      // 탐지 구역번호
    private String dl_violation_type;               // 위반 유형
    private String dl_car_number;                   // 인식 차량 번호
    private String dl_image_path;                   // 탐지 이미지 경로
    private LocalDateTime dl_first_detected_at;     // 최초 탐지 시간
    private LocalDateTime  dl_last_detected_at;     // 마지막 탐지 시간



    public DetectionEntity toEntity() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        return DetectionEntity.builder()
                .dlNo(dl_no)                        // 탐지 기록 번호
                .dlCameraId(dl_camera_id)           // 감지 카메라 ID
                .dlZoneNo(dl_zone_no)               // 탐지 구역번호
                .dlType(dl_violation_type)          // 위반 유형
                .dlCarNumber(dl_car_number)         // 인식 차량 번호
                .dlImage(dl_image_path)             // 탐지 이미지 경로
                .dlFirstTime(dl_first_detected_at)  // 최초 탐지 시간
                .dlLastTime(dl_last_detected_at)    // 마지막 탐지 시간
                .build();

    }

    public static DetectionDto fromEntity(DetectionEntity entity) {

        DetectionDto dto = new DetectionDto();

        dto.setDl_no(entity.getDlNo());
        dto.setDl_camera_id(entity.getDlCameraId());
        dto.setDl_zone_no(entity.getDlZoneNo());
        dto.setDl_violation_type(entity.getDlType());
        dto.setDl_car_number(entity.getDlCarNumber());
        dto.setDl_image_path(entity.getDlImage());
        dto.setDl_first_detected_at(entity.getDlFirstTime());
        dto.setDl_last_detected_at(entity.getDlLastTime());

        return dto;

    }

}

