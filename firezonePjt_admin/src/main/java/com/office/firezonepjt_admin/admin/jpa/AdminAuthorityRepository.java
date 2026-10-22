package com.office.firezonepjt_admin.admin.jpa;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AdminAuthorityRepository extends JpaRepository<AdminAuthorityEntity, Integer> {

    Optional<AdminAuthorityEntity> findByRoleNameIgnoreCase(String roleName);
}
