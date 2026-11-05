package com.office.firezonepjt_admin.admin.jpa;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.JoinTable;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "user_member")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserMemberEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "um_no")
    private int userNo;

    @Column(name = "um_id", nullable = false, length = 20)
    private String userId;

    @Column(name = "um_pw", nullable = false, length = 100)
    private String password;

    @Column(name = "um_name", nullable = false, length = 20)
    private String name;

    @Column(name = "um_mail", nullable = false, length = 20)
    private String email;

    @Column(name = "um_phone", nullable = false, length = 20)
    private String phone;

    @ManyToOne(fetch = FetchType.LAZY)
    private AuthorityEntity authorityEntity;

    @Column(name = "um_reg_date", updatable = false)
    private LocalDateTime registeredAt;

    @Column(name = "um_mod_date")
    private LocalDateTime modifiedAt;
}
