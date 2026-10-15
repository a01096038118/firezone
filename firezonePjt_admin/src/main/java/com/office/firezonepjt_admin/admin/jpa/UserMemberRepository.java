package com.office.firezonepjt_admin.admin.jpa;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface UserMemberRepository extends JpaRepository<UserMemberEntity, Integer> {

    @EntityGraph(attributePaths = "authorityEntity")
    List<UserMemberEntity> findAllByOrderByUserNoDesc();

    @EntityGraph(attributePaths = "authorityEntity")
    Optional<UserMemberEntity> findByUserNo(int userNo);

    @Modifying
    @Query(value = "DELETE FROM user_member_authority WHERE um_no = :userNo", nativeQuery = true)
    int deleteAuthorityLinkByUserNo(@Param("userNo") int userNo);
}
