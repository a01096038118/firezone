package com.office.firezonepjt.user;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.format.DateTimeFormatter;

@Repository
public class MemberDao {

    final private String CLASS_NAME = "[MemberDao] ";
    private static final DateTimeFormatter DATE_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    final private JdbcTemplate jdbcTemplate;

    public MemberDao(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public boolean isMember(String id) {
        System.out.println(CLASS_NAME.concat("isMember()"));

        String sql = "SELECT COUNT(*) FROM USER_MEMBER WHERE UM_ID = ?";

        int result = jdbcTemplate.queryForObject(sql, Integer.class, id);
        if (result > 0)
            return true;
        else
            return false;

    }

    public int insertMember(MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("insertMember()"));

        String sql = "INSERT INTO USER_MEMBER(UM_ID, UM_PW, UM_NAME, UM_MAIL, UM_PHONE) " +
                     "VALUES(?, ?, ?, ?)";

        int result = -1;
        try {
            result = jdbcTemplate.update(sql,
                                            memberDto.getUm_id(),
                                            memberDto.getUm_pw(),
                                            memberDto.getUm_name(),
                                            memberDto.getUm_mail(),
                                            memberDto.getUm_phone());
        } catch (Exception e) {
            e.printStackTrace();

        }

        return result;

    }

    public MemberDto selectMemberByID(String id) {
        System.out.println(CLASS_NAME.concat("isMember()"));

        String sql = "SELECT * FROM USER_MEMBER WHERE UM_ID = ?";
        return jdbcTemplate.query(sql, this::mapMember, id)
                .stream()
                .findFirst()
                .orElse(null);

    }

    public int updateMember(MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("updateMember()"));

        String sql =    "UPDATE " +
                            "USER_MEMBER " +
                        "SET " +
                            "UM_PW = ?, " +
                            "UM_NAME = ?," +
                            "UM_MAIL = ?, " +
                            "UM_PHONE = ? " +
                        "WHERE " +
                            "UM_NO = ?";

        int result = -1;
        try {
            result = jdbcTemplate.update(sql,
                                            memberDto.getUm_pw(),
                                            memberDto.getUm_name(),
                                            memberDto.getUm_mail(),
                                            memberDto.getUm_phone(),
                                            memberDto.getUm_no());

        } catch (Exception e) {
            e.printStackTrace();

        }

        return result;

    }

    public MemberDto selectMemberByIDAndMail(MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("selectMemberByIDAndMail()"));

        String sql = "SELECT " +
                     "* " +
                    "FROM " +
                        "USER_MEMBER " +
                    "WHERE " +
                        "UM_ID=? AND UM_NAME=? AND UM_MAIL=?";

        return jdbcTemplate.query(
                        sql,
                        this::mapMember,
                        memberDto.getUm_id(),
                        memberDto.getUm_name(),
                        memberDto.getUm_mail())
                .stream()
                .findFirst()
                .orElse(null);

    }

    private MemberDto mapMember(ResultSet rs, int rowNum) throws SQLException {
        MemberDto memberDto = new MemberDto();
        memberDto.setUm_no(rs.getInt("UM_NO"));
        memberDto.setUm_id(rs.getString("UM_ID"));
        memberDto.setUm_pw(rs.getString("UM_PW"));
        memberDto.setUm_name(rs.getString("UM_NAME"));
        memberDto.setUm_mail(rs.getString("UM_MAIL"));
        memberDto.setUm_phone(rs.getString("UM_PHONE"));

        var regDate = rs.getTimestamp("UM_REG_DATE");
        if (regDate != null) {
            memberDto.setUm_reg_date(regDate.toLocalDateTime().format(DATE_FORMATTER));
        }

        var modDate = rs.getTimestamp("UM_MOD_DATE");
        if (modDate != null) {
            memberDto.setUm_mod_date(modDate.toLocalDateTime().format(DATE_FORMATTER));
        }

        return memberDto;
    }

    public int updatePassword(String id, String encodedNewPw) {
        System.out.println(CLASS_NAME.concat("updatePassword()"));

        String sql = "UPDATE USER_MEMBER SET UM_PW = ? WHERE UM_ID = ?";

        int result = -1;
        try {
            result = jdbcTemplate.update(sql, encodedNewPw, id);

        } catch (Exception e) {
            e.printStackTrace();

        }

        return result;

    }
}
