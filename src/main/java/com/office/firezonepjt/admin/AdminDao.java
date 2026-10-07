package com.office.firezonepjt.admin;

import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;

@Repository
public class AdminDao {

    final private String CLASS_NAME = "[AdminDao] ";

    final private JdbcTemplate jdbcTemplate;

    public AdminDao(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public boolean isAdmin(String id) {
        System.out.println(CLASS_NAME.concat("isAdmin()"));

        String sql = "SELECT COUNT(*) FROM admin_member WHERE ID = ?";

        int result = jdbcTemplate.queryForObject(sql, Integer.class, id);
        if (result > 0)
            return true;
        else
            return false;

    }

    public int insertAdmin(AdminDto adminDto) {
        System.out.println(CLASS_NAME.concat("insertAdmin()"));

        String sql = "INSERT INTO admin_member(am_id, am_pw, am_name, am_mail, am_phone) " +
                "VALUES(?, ?, ?, ?)";

        int result = -1;
        try {
            result = jdbcTemplate.update(sql,
                    adminDto.getAm_id(),
                    adminDto.getAm_pw(),
                    adminDto.getAm_name(),
                    adminDto.getAm_mail(),
                    adminDto.getAm_phone());
        } catch (Exception e) {
            e.printStackTrace();

        }

        return result;

    }

    public AdminDto selectAdminByID(String id) {
        System.out.println(CLASS_NAME.concat("selectAdminByID()"));

        String sql = "SELECT * FROM admin_member WHERE am_id = ?";

        List<AdminDto> adminDtos = new ArrayList<>();

        try {
            adminDtos = jdbcTemplate.query(sql, (rs, rowNum) -> {

                AdminDto adminDto = new AdminDto();

                adminDto.setAm_id(rs.getString("am_id"));
                adminDto.setAm_pw(rs.getString("am_pw"));
                adminDto.setAm_name(rs.getString("am_name"));
                adminDto.setAm_mail(rs.getString("am_mail"));
                adminDto.setAm_phone(rs.getString("am_phone"));

                return adminDto;
            }, id);

        } catch (DataAccessException e) {
            e.printStackTrace();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return adminDtos.size() > 0 ? adminDtos.get(0) : null;
    }

    public int updateAdmin(AdminDto adminDto) {
        System.out.println(CLASS_NAME.concat("updateAdmin()"));

        String sql =    "UPDATE " +
                "admin_member " +
                "SET " +
                "am_pw = ?, " +
                "am_name = ?, " +
                "am_mail = ?, " +
                "am_phone = ? " +
                "WHERE " +
                "am_no = ?";

        int result = -1;
        try {
            result = jdbcTemplate.update(sql,
                    adminDto.getAm_pw(),
                    adminDto.getAm_mail(),
                    adminDto.getAm_mail(),
                    adminDto.getAm_phone(),
                    adminDto.getAm_no());

        } catch (Exception e) {
            e.printStackTrace();

        }

        return result;

    }

    public AdminDto selectAdminByIDAndMail(AdminDto memberDto) {
        System.out.println(CLASS_NAME.concat("selectAdminByIDAndMail()"));

        String sql = "SELECT * " +
                "FROM admin_member " +
                "WHERE am_id = ? AND am_mail = ?";

        try {

            return jdbcTemplate.queryForObject(sql, (rs, rowNum) -> {

                AdminDto adminDto = new AdminDto();

                adminDto.setAm_id(rs.getString("am_id"));
                adminDto.setAm_pw(rs.getString("am_pw"));
                adminDto.setAm_name(rs.getString("am_name"));
                adminDto.setAm_mail(rs.getString("am_mail"));
                adminDto.setAm_phone(rs.getString("am_phone"));

                return adminDto;

            }, memberDto.getAm_id(), memberDto.getAm_mail());

        } catch (DataAccessException e) {
            e.printStackTrace();
            return null;
        }
    }

    public int updatePassword(String id, String encodedNewPw) {
        System.out.println(CLASS_NAME.concat("updatePassword()"));

        String sql = "UPDATE admin_member SET am_pw = ? WHERE am_id = ?";

        int result = -1;
        try {
            result = jdbcTemplate.update(sql, encodedNewPw, id);

        } catch (Exception e) {
            e.printStackTrace();

        }

        return result;

    }
}