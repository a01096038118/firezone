package com.office.firezonepjt.admin;

import com.office.firezonepjt.admin.jpa.AdminEntity;
import lombok.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

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

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        return AdminEntity.builder()
                .adNo(am_no)
                .adId(am_id)
                .adPw(am_pw)
                .adMail(am_mail)
                .adPhone(am_phone)
                .adRegDate(am_reg_date != null ? LocalDateTime.parse(am_reg_date, formatter) : null)
                .adModDate(am_mod_date != null ? LocalDateTime.parse(am_mod_date, formatter) : null)
                .build();

    }

}
