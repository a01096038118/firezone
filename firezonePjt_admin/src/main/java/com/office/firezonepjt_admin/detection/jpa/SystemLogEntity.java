package com.office.firezonepjt_admin.detection.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Table(name = "system_log")
public class SystemLogEntity {


    @Id
    @Column(name = "sl_no")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int slNo;                   // 시스템 로그 번호

    @Column(name = "sl_action", nullable = false, length = 100)
    private String slAction;            // 시스템 활동 내역

    @Column(name = "sl_created_at", nullable = false)
    private LocalDateTime slCreated;    // 로그 발생 시간

}
