package com.office.firezonepjt.user.jpa;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "admin_authority", uniqueConstraints = {
        @UniqueConstraint(columnNames = "aa_role_name")
})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthorityEntity {

    @Id
    @Column(name="aa_no")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int authNo;                // 권한 고유 번호

    @Column(name="aa_role_name", nullable = false, length = 20)
    private String authRoleName;        // 권한 이름

    public AuthorityDto toDto() {
        return AuthorityDto.builder()
                .aa_no(authNo)
                .aa_role_name(authRoleName)
                .build();
    }

}
