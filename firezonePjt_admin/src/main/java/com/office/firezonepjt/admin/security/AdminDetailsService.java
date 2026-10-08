package com.office.firezonepjt_admin.admin.security;

import com.office.firezonepjt.admin.jpa.AdminEntity;
import com.office.firezonepjt.admin.jpa.AdminRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Slf4j
@Service
public class AdminDetailsService implements UserDetailsService {

    final private AdminRepository adminRepository;

    public AdminDetailsService(AdminRepository adminRepository) {
        this.adminRepository = adminRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        log.info("loadUserByUsername()");

        Optional<AdminEntity> optionalMember = adminRepository.findByAdId(username);
        if (optionalMember.isPresent()) {
            AdminEntity findedMemberEntity = optionalMember.get();
            return User.builder()
                    .username(findedMemberEntity.getAdId())
                    .password(findedMemberEntity.getAdPw())
                    .build();
        }

        return null;

    }

}
