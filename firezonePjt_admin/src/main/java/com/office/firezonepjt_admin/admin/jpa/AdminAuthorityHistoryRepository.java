package com.office.firezonepjt_admin.admin.jpa;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AdminAuthorityHistoryRepository extends JpaRepository<AdminAuthorityHistoryEntity, Integer> {

    Optional<AdminAuthorityHistoryEntity> findFirstByAdminNoOrderByChangedAtDescHistoryNoDesc(int adminNo);
}
