package com.office.firezonepjt.user.jpa;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AuthorityRepository extends JpaRepository<AuthorityEntity, Integer> {

    Optional<AuthorityEntity> findByAuthRoleName(String authRoleName);

    boolean existsByAuthRoleName(String authRoleName);

}
