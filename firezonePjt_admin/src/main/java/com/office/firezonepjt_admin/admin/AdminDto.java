package com.office.firezonepjt_admin.admin;

import com.office.firezonepjt_admin.admin.jpa.AdminEntity;
import lombok.*;

import java.time.LocalDateTime;

//@Getter
//@Setter
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AdminDto {

    private int am_no;
    private String am_id;
    private String am_pw;
    private String am_name;
    private String am_mail;
    private String am_phone;
    private String am_reg_date;
    private String am_mod_date;
    private int historyNo;
    private int historyAdminNo;
    private String historyAdminId;
    private Integer beforeAuthorityNo;
    private String beforeRoleName;
    private int afterAuthorityNo;
    private String afterRoleName;
    private int changedBy;
    private String changedById;
    private LocalDateTime changedAt;

    public AdminDto(
            int historyNo,
            int historyAdminNo,
            String historyAdminId,
            Integer beforeAuthorityNo,
            String beforeRoleName,
            int afterAuthorityNo,
            String afterRoleName,
            int changedBy,
            String changedById,
            LocalDateTime changedAt) {
        this.historyNo = historyNo;
        this.historyAdminNo = historyAdminNo;
        this.historyAdminId = historyAdminId;
        this.beforeAuthorityNo = beforeAuthorityNo;
        this.beforeRoleName = beforeRoleName;
        this.afterAuthorityNo = afterAuthorityNo;
        this.afterRoleName = afterRoleName;
        this.changedBy = changedBy;
        this.changedById = changedById;
        this.changedAt = changedAt;
    }

    public int getAm_no() {
        return am_no;
    }

    public void setAm_no(int am_no) {
        this.am_no = am_no;
    }

    public String getAm_id() {
        return am_id;
    }

    public void setAm_id(String am_id) {
        this.am_id = am_id;
    }

    public String getAm_pw() {
        return am_pw;
    }

    public void setAm_pw(String am_pw) {
        this.am_pw = am_pw;
    }

    public String getAm_name() {
        return am_name;
    }

    public void setAm_name(String am_name) {
        this.am_name = am_name;
    }

    public String getAm_mail() {
        return am_mail;
    }

    public void setAm_mail(String am_mail) {
        this.am_mail = am_mail;
    }

    public String getAm_phone() {
        return am_phone;
    }

    public void setAm_phone(String am_phone) {
        this.am_phone = am_phone;
    }

    public String getAm_reg_date() {
        return am_reg_date;
    }

    public void setAm_reg_date(String am_reg_date) {
        this.am_reg_date = am_reg_date;
    }

    public String getAm_mod_date() {
        return am_mod_date;
    }

    public void setAm_mod_date(String am_mod_date) {
        this.am_mod_date = am_mod_date;
    }

    public AdminEntity toEntity() {
        return AdminEntity.builder()
                .adNo(am_no)
                .adId(am_id)
                .adPw(am_pw)
                .adName(am_name)
                .adMail(am_mail)
                .adPhone(am_phone)
                .build();
    }

}
