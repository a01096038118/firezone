package com.office.firezonepjt_admin.detection;

import com.office.firezonepjt_admin.detection.jpa.SystemLogEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class SystemLogDto {

    private int sl_no;                      // 시스템 로그 번호
    private String sl_action;               // 시스템 활동 내역
    private LocalDateTime sl_created_at;    // 로그 발생 시간

    public SystemLogEntity logEntity() {

        return SystemLogEntity.builder()
                .slNo(sl_no)                // 시스템 로그 번호
                .slAction(sl_action)        // 시스템 활동 내역
                .slCreated(sl_created_at)   // 로그 발생 시간
                .build();

    }

}



