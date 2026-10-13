package com.office.firezonepjt.user.security;

import com.office.firezonepjt.user.jpa.MemberEntity;
import com.office.firezonepjt.user.jpa.MemberRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class MemberDetailsService implements UserDetailsService {

    final private MemberRepository memberRepository;

    public MemberDetailsService(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        log.info("loadUserByUsername()");

        return memberRepository.findByMemId(username)
                .map(member -> {
                    if (member.getAuthorityEntity() == null
                            || member.getAuthorityEntity().getAuthRoleName() == null
                            || member.getAuthorityEntity().getAuthRoleName().isBlank()) {
                        throw new IllegalStateException(
                                "회원의 권한 정보가 설정되어 있지 않습니다: " + username);
                    }

                    String role = member.getAuthorityEntity().getAuthRoleName();
                    if (role.startsWith("ROLE_")) {
                        role = role.substring("ROLE_".length());
                    }

                    return User.builder()
                            .username(member.getMemId())
                            .password(member.getMemPw())
                            .roles(role)
                            .build();
                })
                .orElseThrow(() -> new UsernameNotFoundException(
                        "회원 정보를 찾을 수 없습니다: " + username));

    }

}
