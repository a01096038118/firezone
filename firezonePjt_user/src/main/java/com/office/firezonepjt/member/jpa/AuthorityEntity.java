package com.office.firezonepjt.member.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "USER_AUTHORITY", uniqueConstraints = {@UniqueConstraint(columnNames = "ROLE_NAME")})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthorityEntity {

    @Id
    @Column(name="NO")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private byte authNo;                // 권한 고유 번호

    @Column(name="ROLE_NAME", nullable = false, length = 20)
    private String authRoleName;        // 권한 이름

    public AuthorityDto toDto() {
        return AuthorityDto.builder()
                .no(authNo)
                .role_name(authRoleName)
                .build();
    }

}
