package com.office.firezonepjt.user.jpa;

import com.office.firezonepjt.user.MemberDto;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Entity
@Table(name = "user_member", uniqueConstraints = {@UniqueConstraint(columnNames = "um_id")})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MemberEntity {

    @Id
    @Column(name = "um_no")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int memNo;                 // 사용자 고유 번호

    @Column(name = "um_id", nullable = false, length = 20)
    private String memId;              // 사용자 아이디

    @Column(name = "um_pw", nullable = false, length = 100)
    private String memPw;              // 사용자 비밀번호

    @Column(name = "um_name", nullable = false, length = 20)
    private String memName;              // 사용자 비밀번호

    @Column(name = "um_mail", nullable = false, length = 20)
    private String memMail;            // 사용자 메일

    @Column(name = "um_phone", nullable = false, length = 20)
    private String memPhone;           // 사용자 연락처

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    private AuthorityEntity authorityEntity;

    @Column(name = "um_reg_date", updatable = false)
    private LocalDateTime memRegDate;        // 사용자 정보 등록일

    @Column(name = "um_mod_date")
    private LocalDateTime memModDate;        // 사용자 정보 수정일

    @PrePersist
    protected void onCreate() {
        this.memRegDate = LocalDateTime.now();
        this.memModDate = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        this.memModDate = LocalDateTime.now();
    }

    public MemberDto toDto() {

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        return MemberDto.builder()
                .um_no(memNo)
                .um_id(memId)
                .um_pw(memPw)
                .um_name(memName)
                .um_mail(memMail)
                .um_phone(memPhone)
                .authorityDto(authorityEntity != null ? authorityEntity.toDto() : null)
                .um_reg_date(memRegDate != null ? memRegDate.format(formatter) : null)
                .um_mod_date(memModDate != null ? memModDate.format(formatter) : null)
                .build();


    }

}
