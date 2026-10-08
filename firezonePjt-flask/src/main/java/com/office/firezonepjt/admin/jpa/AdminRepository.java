package com.office.firezonepjt.admin.jpa;

import com.office.firezonepjt.admin.jpa.AdminEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AdminRepository extends JpaRepository<AdminEntity, Integer> {

    // 어드민 ID 중복 체크
    public boolean existsByAdId(String memId);

    // 어드민 ID로 어드민 조회
    public Optional<AdminEntity> findByAdId(String memId);

    // 어드민 ID와 MAIL로 어드민 조회(인증)
    public Optional<AdminEntity> findByAdIdAndAdMail(String memId, String memMail);

}
