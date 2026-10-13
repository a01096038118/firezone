package com.office.firezonepjt.user.jpa;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthorityDto {

    private int aa_no;              // 권한 고유 번호
    private String aa_role_name;    // 권한 이름

    public AuthorityEntity toEntity() {
        return AuthorityEntity.builder()
                .authNo(aa_no)
                .authRoleName(aa_role_name)
                .build();
    }

}
