package com.office.firezonepjt_admin.admin.jpa;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AuthorityRepository extends JpaRepository<AuthorityEntity, Integer> {

    Optional<AuthorityEntity> findByRoleNameIgnoreCase(String roleName);
}
