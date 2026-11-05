package com.office.firezonepjt.user.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.EntityGraph;

import java.util.Optional;

public interface MemberRepository extends JpaRepository<MemberEntity, Integer> {

    // 회원 ID 중복 체크
    public boolean existsByMemId(String memId);

    // 회원ID로 회원 조회
    @EntityGraph(attributePaths = "authorityEntity")
    public Optional<MemberEntity> findByMemId(String memId);

    // 회원ID와 MAIL로 회원 조회(인증)
    public Optional<MemberEntity> findByMemIdAndMemMail(String memId, String memMail);

}
