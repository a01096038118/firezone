package com.office.firezonepjt_admin.admin.jpa;

import com.office.firezonepjt_admin.admin.AdminDto;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface AdminAuthorityHistoryRepository extends JpaRepository<AdminAuthorityHistoryEntity, Integer> {

    Optional<AdminAuthorityHistoryEntity> findFirstByAdminNoOrderByChangedAtDescHistoryNoDesc(int adminNo);

    @Query("""
            select new com.office.firezonepjt_admin.admin.AdminDto(
                history.historyNo,
                history.adminNo,
                admin.adId,
                history.beforeAuthorityNo,
                coalesce(beforeAuthority.roleName, '없음'),
                history.afterAuthorityNo,
                coalesce(afterAuthority.roleName, '삭제된 권한'),
                history.changedBy,
                coalesce(changedByAdmin.adId, '삭제된 관리자'),
                history.changedAt
            )
            from AdminAuthorityHistoryEntity history
            join history.admin admin
            left join history.beforeAuthority beforeAuthority
            left join history.afterAuthority afterAuthority
            left join history.changedByAdmin changedByAdmin
            where history.adminNo = :adminNo
            order by history.changedAt desc, history.historyNo desc
            """)
    List<AdminDto> findPermissionHistory(@Param("adminNo") int adminNo);

    @Query(value = """
            SELECT CASE WHEN COUNT(*) > 0 THEN TRUE ELSE FALSE END
            FROM admin_authority_history current_history
            JOIN admin_authority authority
              ON authority.aa_no = current_history.aah_after_auth_no
            WHERE current_history.aah_admin_no <> :excludedAdminNo
              AND UPPER(authority.aa_role_name) = 'MASTER'
              AND current_history.aah_no = (
                  SELECT latest_history.aah_no
                  FROM admin_authority_history latest_history
                  WHERE latest_history.aah_admin_no = current_history.aah_admin_no
                  ORDER BY latest_history.aah_changed_at DESC, latest_history.aah_no DESC
                  LIMIT 1
              )
            """, nativeQuery = true)
    boolean existsAnotherCurrentMaster(@Param("excludedAdminNo") int excludedAdminNo);
}
