package com.office.firezonepjt.user;

import com.office.firezonepjt.user.jpa.MemberEntity;
import com.office.firezonepjt.user.jpa.MemberRepository;
import com.office.firezonepjt.user.jpa.AuthorityEntity;
import com.office.firezonepjt.user.jpa.AuthorityRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.util.Optional;

@Slf4j
@Service
//@RequiredArgsConstructor
public class MemberService {

    final private String CLASS_NAME = "[MemberService] ";

    final public static int USER_ID_ALREADY_EXIST   = 0;
    final public static int USER_SIGNUP_SUCCESS     = 1;
    final public static int USER_SIGNUP_FAIL        = -1;

    final public static int MODIFY_SUCCESS          = 1;
    final public static int MODIFY_FAIL             = 0;

    final public static int NEW_PASSWORD_CREATION_SUCCESS   = 1;
    final public static int NEW_PASSWORD_CREATION_FAIL      = 0;

    final private MemberDao memberDao;
    final private PasswordEncoder passwordEncoder;
    final private JavaMailSender javaMailSender;
    final private MemberRepository memberRepository;
    final private AuthorityRepository authorityRepository;
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    public MemberService(MemberDao memberDao,
                         PasswordEncoder passwordEncoder,
                         JavaMailSender javaMailSender,
                         MemberRepository memberRepository,
                         AuthorityRepository authorityRepository) {
        this.memberDao = memberDao;
        this.passwordEncoder = passwordEncoder;
        this.javaMailSender = javaMailSender;
        this.memberRepository = memberRepository;
        this.authorityRepository = authorityRepository;
    }


    @Transactional
    public int signupConfirm(MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("signupConfirm()"));

//        boolean isMember = memberDao.isMember(memberDto.getId());
//        boolean isMember = memberMapper.isMember(memberDto.getId());
        boolean isMember = memberRepository.existsByMemId(memberDto.getUm_id());

        if (!isMember) {
            String encodedPW = passwordEncoder.encode(memberDto.getUm_pw());
            memberDto.setUm_pw(encodedPW);
            MemberEntity memberEntity = memberDto.toEntity();
            AuthorityEntity defaultAuthority = authorityRepository.findByAuthRoleName("PRE_USER")
                    .orElseGet(() -> authorityRepository.save(AuthorityEntity.builder()
                            .authRoleName("PRE_USER")
                            .build()));
            memberEntity.setAuthorityEntity(defaultAuthority);
            MemberEntity savedMemberEntity = memberRepository.save(memberEntity);

            if (savedMemberEntity != null)
                return USER_SIGNUP_SUCCESS;
            else
                return USER_SIGNUP_FAIL;

        } else {
            return USER_ID_ALREADY_EXIST;
        }

    }

    public String signinConfirm(MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("signinConfirm()"));

        Optional<MemberEntity> optionalMember =
                memberRepository.findByMemId(memberDto.getUm_id());
        if (optionalMember.isPresent() &&
                    passwordEncoder.matches(memberDto.getUm_pw(), optionalMember.get().getMemPw())) {
            log.info("MEMBER LOGIN SUCCESS");
            return optionalMember.get().getMemId();

        } else {
            log.info("MEMBER LOGIN FAIL");
            return null;

        }

    }

    public MemberDto modify(String loginedID) {
        System.out.println(CLASS_NAME.concat("modify()"));

        Optional<MemberEntity> optionalMember =
                memberRepository.findByMemId(loginedID);
        if (optionalMember.isPresent()) {
            MemberEntity memberEntity = optionalMember.get();
            return memberEntity.toDto();

        }

        return  null;

    }

    @Transactional
    public int modifyConfirm(String loginedID, MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("modifyConfirm()"));

        if (memberDto.getUm_name() == null || memberDto.getUm_name().isBlank()
                || memberDto.getUm_mail() == null || memberDto.getUm_mail().isBlank()
                || memberDto.getUm_phone() == null || memberDto.getUm_phone().isBlank()) {
            return MODIFY_FAIL;
        }

        Optional<MemberEntity> optionalMember =
                memberRepository.findByMemId(loginedID);
        if (optionalMember.isPresent()) {
            MemberEntity memberEntity = optionalMember.get();
            if (memberDto.getUm_pw() != null && !memberDto.getUm_pw().isBlank()) {
                memberEntity.setMemPw(passwordEncoder.encode(memberDto.getUm_pw()));
            }
            memberEntity.setMemName(memberDto.getUm_name());
            memberEntity.setMemMail(memberDto.getUm_mail());
            memberEntity.setMemPhone(memberDto.getUm_phone());

            return MODIFY_SUCCESS;

        } else {
            return MODIFY_FAIL;

        }

    }

    @Transactional
    public boolean withdraw(String loginedID, String currentPassword) {
        if (currentPassword == null || currentPassword.isBlank()) {
            return false;
        }

        Optional<MemberEntity> optionalMember = memberRepository.findByMemId(loginedID);
        if (optionalMember.isEmpty()
                || !passwordEncoder.matches(currentPassword, optionalMember.get().getMemPw())) {
            return false;
        }

        MemberEntity member = optionalMember.get();
        memberRepository.deleteAuthorityLinkByMemberNo(member.getMemNo());
        memberRepository.delete(member);
        return true;
    }

    @Transactional
    public int findpasswordConfirm(MemberDto memberDto) {
        System.out.println(CLASS_NAME.concat("findpasswordConfirm()"));

        Optional<MemberEntity> optionalMember =
                memberRepository.findByMemIdAndMemMail(memberDto.getUm_id(), memberDto.getUm_mail());
        if (optionalMember.isPresent()) {
            String newPassword = createNewPassword();
            MemberEntity findedMemberEntity = optionalMember.get();
            findedMemberEntity.setMemPw(passwordEncoder.encode(newPassword));

            MemberEntity updateMember = memberRepository.save(findedMemberEntity);
            if (updateMember != null)
                sendNewPasswordByMail(memberDto.getUm_mail(), newPassword);

            return NEW_PASSWORD_CREATION_SUCCESS;

        }

        return NEW_PASSWORD_CREATION_FAIL;

    }

    private String createNewPassword() {
        System.out.println("[MemberService] createNewPassword()");

        char[] chars = {
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                'u', 'v', 'w', 'x', 'y', 'z'
        };

        StringBuilder password = new StringBuilder(12);
        for (int i = 0; i < 12; i++) {
                char character = chars[SECURE_RANDOM.nextInt(chars.length)];
                password.append(i % 2 == 0 ? Character.toUpperCase(character) : character);
        }

        return password.toString();

    }

    private void sendNewPasswordByMail(String toMailAddr, String newPassword) {
        System.out.println("[MemberService] sendNewPasswordByMail()");

        SimpleMailMessage simpleMailMessage = new SimpleMailMessage();
        simpleMailMessage.setTo(toMailAddr);
        simpleMailMessage.setSubject("[Firezone] 새 비밀번호 안내입니다.");
        simpleMailMessage.setText("새 비밀번호: " + newPassword);

        javaMailSender.send(simpleMailMessage);

    }

}
