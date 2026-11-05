package com.office.firezonepjt_admin.admin.jpa;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserMemberRepository extends JpaRepository<UserMemberEntity, Integer> {

    @EntityGraph(attributePaths = "authorityEntity")
    Optional<UserMemberEntity> findByUserNo(int userNo);
}
