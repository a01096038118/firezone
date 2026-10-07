package com.office.firezonepjt.admin;

import com.office.firezonepjt.admin.jpa.AdminEntity;
import com.office.firezonepjt.admin.jpa.AdminRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.util.Date;
import java.util.Optional;

@Slf4j
@Service
public class AdminService {


    final private String CLASS_NAME = "[MemberService] ";

    final public static int ADMIN_ID_ALREADY_EXIST   = 0;
    final public static int ADMIN_SIGNUP_SUCCESS     = 1;
    final public static int ADMIN_SIGNUP_FAIL        = -1;

    final public static int MODIFY_SUCCESS          = 1;
    final public static int MODIFY_FAIL             = 0;

    final public static int NEW_PASSWORD_CREATION_SUCCESS   = 1;
    final public static int NEW_PASSWORD_CREATION_FAIL      = 0;

    final private AdminDao adminDao;
    final private PasswordEncoder passwordEncoder;
    final private JavaMailSender javaMailSender;
    final private AdminRepository adminRepository;

    public AdminService(AdminDao adminDao,
                         PasswordEncoder passwordEncoder,
                         JavaMailSender javaMailSender,
                         AdminRepository adminRepository) {
        this.adminDao = adminDao;
        this.passwordEncoder = passwordEncoder;
        this.javaMailSender = javaMailSender;
        this.adminRepository = adminRepository;
    }


    public int signupConfirm(AdminDto adminDto) {
        System.out.println(CLASS_NAME.concat("signupConfirm()"));

        boolean isAdmin = adminRepository.existsByAdId(adminDto.getAm_id());

        if (!isAdmin) {
            String encodedPW = passwordEncoder.encode(adminDto.getAm_pw());
            adminDto.setAm_pw(encodedPW);

            AdminEntity savedAdminEntity = adminRepository.save(adminDto.toEntity());

            if (savedAdminEntity != null)
                return ADMIN_SIGNUP_SUCCESS;
            else
                return ADMIN_SIGNUP_FAIL;

        } else {
            return ADMIN_ID_ALREADY_EXIST;
        }

    }

    public String signinConfirm(AdminDto adminDto) {
        System.out.println(CLASS_NAME.concat("signinConfirm()"));

//        MemberDto dto = memberDao.selectMemberByID(memberDto.getId());
        /*
        MemberDto dto = memberMapper.selectMemberByID(memberDto.getId());
        if (dto != null && passwordEncoder.matches(memberDto.getPw(), dto.getPw())) {
            System.out.println(CLASS_NAME.concat("MEMBER LOGIN SUCCESS!!"));
            return dto.getId();

        } else {
            System.out.println(CLASS_NAME.concat("MEMBER LOGIN FAIL!!"));
            return null;

        }
        */

        Optional<AdminEntity> optionalMember =
                adminRepository.findByAdId(adminDto.getAm_id());
        if (optionalMember.isPresent() &&
                passwordEncoder.matches(adminDto.getAm_pw(), optionalMember.get().getAdPw())) {
            log.info("ADMIN LOGIN SUCCESS");
            return optionalMember.get().getAdId();

        } else {
            log.info("ADMIN LOGIN FAIL");
            return null;

        }

    }

    public AdminDto modify(String loginedID) {
        System.out.println(CLASS_NAME.concat("modify()"));

//        return memberDao.selectMemberByID(loginedID);
//        return memberMapper.selectMemberByID(loginedID);

        Optional<AdminEntity> optionalMember =
                adminRepository.findByAdId(loginedID);
        if (optionalMember.isPresent()) {
            AdminEntity adminEntity = optionalMember.get();

            return adminEntity.toDto();

        }

        return  null;

    }

    @Transactional
    public int modifyConfirm(AdminDto adminDto) {
        System.out.println(CLASS_NAME.concat("modifyConfirm()"));

        String encodedPW = passwordEncoder.encode(adminDto.getAm_pw());
        adminDto.setAm_pw(encodedPW);

        Optional<AdminEntity> optionalAdmin =
                adminRepository.findById(adminDto.getAm_no());
        if (optionalAdmin.isPresent()) {
            AdminEntity adminEntity = optionalAdmin.get();
            adminEntity.setAdPw(adminDto.getAm_pw());
            adminEntity.setAdMail(adminDto.getAm_mail());
            adminEntity.setAdPhone(adminDto.getAm_phone());

            return MODIFY_SUCCESS;

        } else {
            return MODIFY_FAIL;

        }

    }

    public int findpasswordConfirm(AdminDto adminDto) {
        System.out.println(CLASS_NAME.concat("findpasswordConfirm()"));

        Optional<AdminEntity> optionalAdmin =
                adminRepository.findByAdIdAndAdMail(adminDto.getAm_id(), adminDto.getAm_mail());
        if (optionalAdmin.isPresent()) {
            String newPassword = createNewPassword();
            AdminEntity findedAdminEntity = optionalAdmin.get();
            findedAdminEntity.setAdPw(passwordEncoder.encode(newPassword));

            AdminEntity updateAdmin = adminRepository.save(findedAdminEntity);
            if (updateAdmin != null)
                sendNewPasswordByMail(adminDto.getAm_mail(), newPassword);

            return NEW_PASSWORD_CREATION_SUCCESS;

        }

        return NEW_PASSWORD_CREATION_FAIL;

    }

    private String createNewPassword() {
        System.out.println(CLASS_NAME.concat("createNewPassword()");

        char[] chars = new char[] {
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                'u', 'v', 'w', 'x', 'y', 'z'
        };

        StringBuffer stringBuffer = new StringBuffer();
        SecureRandom secureRandom = new SecureRandom();
        secureRandom.setSeed(new Date().getTime());

        int index = 0;
        int length = chars.length;
        for (int i = 0; i < 8; i++) {
            index = secureRandom.nextInt(length);

            if (index % 2 == 0)
                stringBuffer.append(String.valueOf(chars[index]).toUpperCase());
            else
                stringBuffer.append(String.valueOf(chars[index]).toLowerCase());
        }

        System.out.println(CLASS_NAME.concat("NEW PASSWORD: " + stringBuffer.toString());

        return stringBuffer.toString();

    }

    private void sendNewPasswordByMail(String toMailAddr, String newPassword) {
        System.out.println(CLASS_NAME.concat("sendNewPasswordByMail()");

        SimpleMailMessage simpleMailMessage = new SimpleMailMessage();
        // simpleMailMessage.setTo(toMailAddr);
        simpleMailMessage.setTo("nikecafe@naver.com");
        simpleMailMessage.setSubject("[MyCalendar] 새 비밀번호 안내입니다.");
        simpleMailMessage.setText("새 비밀번호: " + newPassword);
        simpleMailMessage.setFrom("hohasic@gmail.com");

        javaMailSender.send(simpleMailMessage);

    }

}


}
