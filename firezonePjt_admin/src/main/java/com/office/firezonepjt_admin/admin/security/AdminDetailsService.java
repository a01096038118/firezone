package com.office.firezonepjt_admin.admin.security;

import com.office.firezonepjt_admin.admin.AdminService;
import com.office.firezonepjt_admin.admin.AdminService.AdminPermissionRole;
import com.office.firezonepjt_admin.admin.jpa.AdminEntity;
import com.office.firezonepjt_admin.admin.jpa.AdminRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
public class AdminDetailsService implements UserDetailsService {

    final private AdminRepository adminRepository;
    final private AdminService adminService;

    public AdminDetailsService(
            AdminRepository adminRepository,
            AdminService adminService) {
        this.adminRepository = adminRepository;
        this.adminService = adminService;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        log.info("loadUserByUsername()");

        Optional<AdminEntity> optionalMember = adminRepository.findByAdId(username);
        if (optionalMember.isPresent()) {
            AdminEntity findedMemberEntity = optionalMember.get();
            AdminPermissionRole permissionRole =
                    adminService.findCurrentRole(findedMemberEntity.getAdNo());
            List<String> roles = new ArrayList<>();
            roles.add("ADMIN");
            roles.addAll(permissionRole.toSpringRoles());
            return User.builder()
                    .username(findedMemberEntity.getAdId())
                    .password(findedMemberEntity.getAdPw())
                    .roles(roles.toArray(String[]::new))
                    .build();
        }

        throw new UsernameNotFoundException("Admin account not found: " + username);
    }

}
