package com.office.firezonepjt.user.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface MemberRepository extends JpaRepository<MemberEntity, Integer> {

    // 회원 ID 중복 체크
    public boolean existsByMemId(String memId);

    // 회원ID로 회원 조회
    @EntityGraph(attributePaths = "authorityEntity")
    public Optional<MemberEntity> findByMemId(String memId);

    // 회원ID와 MAIL로 회원 조회(인증)
    public Optional<MemberEntity> findByMemIdAndMemMail(String memId, String memMail);

    @Modifying
    @Query(value = "DELETE FROM user_member_authority WHERE um_no = :memberNo", nativeQuery = true)
    int deleteAuthorityLinkByMemberNo(@Param("memberNo") int memberNo);

}
