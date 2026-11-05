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

    private int ua_no;              // 권한 고유 번호
    private String ua_role_name;    // 권한 이름

    public AuthorityEntity toEntity() {
        return AuthorityEntity.builder()
                .authNo(ua_no)
                .authRoleName(ua_role_name)
                .build();
    }

}
