package com.office.firezonepjt_admin.admin.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import jakarta.persistence.LockModeType;
import java.util.List;
import java.util.Optional;

public interface AdminAuthorityRepository extends JpaRepository<AdminAuthorityEntity, Integer> {

    Optional<AdminAuthorityEntity> findByRoleNameIgnoreCase(String roleName);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select authority from AdminAuthorityEntity authority "
            + "where upper(authority.roleName) = upper(:roleName)")
    List<AdminAuthorityEntity> findAllByRoleNameForUpdate(@Param("roleName") String roleName);
}
