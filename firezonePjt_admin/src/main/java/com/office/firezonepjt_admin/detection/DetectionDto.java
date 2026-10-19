package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.DetectionEntity;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;


import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class DetectionDto {

    private int dl_no;                              // 탐지 기록 번호

    @NotBlank(message = "카메라 ID가 필요합니다.")
    @Size(max = 20, message = "카메라 ID는 20자 이하여야 합니다.")
    private String dl_camera_id;                    // 감지 카메라 ID

    @NotBlank(message = "구역번호가 필요합니다.")
    @Size(max = 20, message = "구역번호는 이하여야 합니다.")
    private String dl_zone_no;                      // 탐지 구역번호

    @NotBlank(message = "위반 유형이 필요합니다.")
    @Size(max = 20, message = "위반유형은 30자 이하여야 합니다.")
    private String dl_violation_type;               // 위반 유형

    @NotBlank(message = "차량번호가 필요합니다.")
    @Size(max = 20, message = "차량번호는 20자 이하여야 합니다.")
    private String dl_car_number;                   // 인식 차량 번호

    @NotBlank(message = "이미지 경로값이 필요합니다.")
    @Size(max = 20, message = "이미지 경로는 255자 이하여야 합니다.")
    private String dl_image_path;                   // 탐지 이미지 경로

    @NotNull(message = "최초 탐지시간이 필요합니다.")
    private LocalDateTime dl_first_detected_at;     // 최초 탐지 시간

    @NotNull(message = "마지막 탐지시간이 필요합니다.")
    private LocalDateTime  dl_last_detected_at;     // 마지막 탐지 시간



    public DetectionEntity toEntity() {

        return DetectionEntity.builder()
                //.dlNo(dl_no)                      // 탐지 기록 번호
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

