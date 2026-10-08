package com.office.firezonepjt_admin.admin.jpa;

import com.office.firezonepjt.admin.AdminDto;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Entity
@Table(name = "admin_member", uniqueConstraints = {@UniqueConstraint(columnNames = "am_id")})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AdminEntity {
    @Id
    @Column(name = "am_no")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int adNo;
    @Column(name = "am_id", nullable = false, length = 20)
    private String adId;

    @Column(name = "am_pw", nullable = false, length = 100)
    private String adPw;

    @Column(name = "am_name", nullable = false, length = 20)
    private String adName;

    @Column(name = "am_mail", nullable = false, length = 20)
    private String adMail;

    @Column(name = "am_phone", nullable = false, length = 20)
    private String adPhone;

    @Column(name = "am_reg_date", updatable = false)
    private LocalDateTime adRegDate;        // 사용자 정보 등록일

    @Column(name = "am_mod_date")
    private LocalDateTime adModDate;        // 사용자 정보 수정일

    @PreUpdate
    protected void onUpdate() {
        this.adModDate = LocalDateTime.now();
    }

    public AdminDto toDto() {

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        return AdminDto.builder()
                .am_no(adNo)
                .am_id(adId)
                .am_pw(adPw)
                .am_name(adName)
                .am_mail(adMail)
                .am_phone(adPhone)
                .am_reg_date(adRegDate != null ? adRegDate.format(formatter) : null)
                .am_mod_date(adModDate != null ? adModDate.format(formatter) : null)
                .build();


    }

}
