package com.office.firezonepjt.member;

import com.office.firezonepjt.member.jpa.AuthorityDto;
import com.office.firezonepjt.member.jpa.MemberEntity;
import lombok.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

//@Getter
//@Setter
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MemberDto {

    private int um_no;                 // 사용자 고유 번호
    private String um_id;              // 사용자 아이디
    private String um_pw;              // 사용자 비밀번호
    private String um_mail;            // 사용자 메일
    private String um_name;            // 사용자 이름
    private String um_phone;           // 사용자 연락처
    private AuthorityDto authorityDto;
    private String um_reg_date;        // 사용자 정보 등록일
    private String um_mod_date;        // 사용자 정보 수정일

    public String getUm_mod_date() {
        return um_mod_date;
    }

    public void setUm_mod_date(String um_mod_date) {
        this.um_mod_date = um_mod_date;
    }

    public String getUm_reg_date() {
        return um_reg_date;
    }

    public void setUm_reg_date(String um_reg_date) {
        this.um_reg_date = um_reg_date;
    }

    public AuthorityDto getAuthorityDto() {
        return authorityDto;
    }

    public void setAuthorityDto(AuthorityDto authorityDto) {
        this.authorityDto = authorityDto;
    }

    public String getUm_phone() {
        return um_phone;
    }

    public void setUm_phone(String um_phone) {
        this.um_phone = um_phone;
    }

    public String getUm_name() {
        return um_name;
    }

    public void setUm_name(String um_name) {
        this.um_name = um_name;
    }

    public String getUm_mail() {
        return um_mail;
    }

    public void setUm_mail(String um_mail) {
        this.um_mail = um_mail;
    }

    public String getUm_pw() {
        return um_pw;
    }

    public void setUm_pw(String um_pw) {
        this.um_pw = um_pw;
    }

    public String getUm_id() {
        return um_id;
    }

    public void setUm_id(String um_id) {
        this.um_id = um_id;
    }

    public int getUm_no() {
        return um_no;
    }

    public void setUm_no(int um_no) {
        this.um_no = um_no;
    }

    public MemberEntity toEntity() {

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        return MemberEntity.builder()
                .memNo(um_no)
                .memId(um_id)
                .memPw(um_pw)
                .memName(um_name)
                .memMail(um_mail)
                .memPhone(um_phone)
                // .memAuthorityNo(authority_no)
                .authorityEntity(authorityDto != null ? authorityDto.toEntity() : null)
                .memRegDate(um_reg_date != null ? LocalDateTime.parse(um_reg_date, formatter) : null)
                .memModDate(um_mod_date != null ? LocalDateTime.parse(um_mod_date, formatter) : null)
                .build();

    }

}
