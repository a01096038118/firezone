package com.office.firezonepjt_admin.admin;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

@Repository
public class UserMemberDao {

    private static final String APPROVED_ROLE = "APPR_USER";
    private static final String PENDING_ROLE = "PRE_USER";

    private final JdbcTemplate jdbcTemplate;

    public UserMemberDao(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> findAll() {
        String sql = """
                SELECT
                    M.UM_NO AS userNo,
                    M.UM_ID AS userId,
                    M.UM_NAME AS name,
                    M.UM_MAIL AS email,
                    M.UM_PHONE AS phone,
                    M.UM_REG_DATE AS registeredAt,
                    A.AA_NO AS authorityNo,
                    A.AA_ROLE_NAME AS authorityName
                FROM USER_MEMBER M
                LEFT JOIN USER_MEMBER_AUTHORITY MA ON MA.UM_NO = M.UM_NO
                LEFT JOIN ADMIN_AUTHORITY A ON A.AA_NO = MA.AA_NO
                ORDER BY M.UM_NO DESC
                """;
        return jdbcTemplate.queryForList(sql).stream()
                .map(this::includeAuthorityDto)
                .toList();
    }

    public Optional<Map<String, Object>> findByNo(int userNo) {
        String sql = """
                SELECT
                    M.UM_NO AS userNo,
                    M.UM_ID AS userId,
                    M.UM_NAME AS name,
                    M.UM_MAIL AS email,
                    M.UM_PHONE AS phone,
                    M.UM_REG_DATE AS registeredAt,
                    M.UM_MOD_DATE AS modifiedAt,
                    A.AA_NO AS authorityNo,
                    A.AA_ROLE_NAME AS authorityName
                FROM USER_MEMBER M
                LEFT JOIN USER_MEMBER_AUTHORITY MA ON MA.UM_NO = M.UM_NO
                LEFT JOIN ADMIN_AUTHORITY A ON A.AA_NO = MA.AA_NO
                WHERE M.UM_NO = ?
                """;
        return jdbcTemplate.queryForList(sql, userNo)
                .stream()
                .map(this::includeAuthorityDto)
                .findFirst();
    }

    public boolean approve(int userNo) {
        jdbcTemplate.update(
                "UPDATE ADMIN_AUTHORITY SET AA_ROLE_NAME = ? WHERE UPPER(AA_ROLE_NAME) = ?",
                APPROVED_ROLE,
                APPROVED_ROLE);
        jdbcTemplate.update("""
                INSERT INTO ADMIN_AUTHORITY (AA_ROLE_NAME)
                SELECT ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM ADMIN_AUTHORITY WHERE UPPER(AA_ROLE_NAME) = ?
                )
                """, APPROVED_ROLE, APPROVED_ROLE);

        String sql = """
                UPDATE USER_MEMBER_AUTHORITY member_authority
                JOIN ADMIN_AUTHORITY current_authority
                    ON current_authority.AA_NO = member_authority.AA_NO
                JOIN ADMIN_AUTHORITY approved_authority
                    ON approved_authority.AA_ROLE_NAME = ?
                SET member_authority.AA_NO = approved_authority.AA_NO
                WHERE member_authority.UM_NO = ?
                    AND current_authority.AA_ROLE_NAME = ?
                """;
        return jdbcTemplate.update(sql, APPROVED_ROLE, userNo, PENDING_ROLE) > 0;
    }

    private Map<String, Object> includeAuthorityDto(Map<String, Object> row) {
        Map<String, Object> user = new LinkedHashMap<>(row);
        Map<String, Object> authorityDto = new LinkedHashMap<>();
        authorityDto.put("aa_no", user.remove("authorityNo"));
        authorityDto.put("aa_role_name", user.remove("authorityName"));
        user.put("authorityDto", authorityDto);
        return user;
    }
}
