package com.office.firezonepjt_admin.admin;

import com.office.firezonepjt_admin.admin.jpa.AdminEntity;
import com.office.firezonepjt_admin.admin.jpa.AdminRepository;
import com.office.firezonepjt_admin.admin.jpa.AdminAuthorityEntity;
import com.office.firezonepjt_admin.admin.jpa.AdminAuthorityHistoryEntity;
import com.office.firezonepjt_admin.admin.jpa.AdminAuthorityHistoryRepository;
import com.office.firezonepjt_admin.admin.jpa.AdminAuthorityRepository;
import com.office.firezonepjt_admin.admin.jpa.AuthorityEntity;
import com.office.firezonepjt_admin.admin.jpa.AuthorityRepository;
import com.office.firezonepjt_admin.admin.jpa.UserMemberEntity;
import com.office.firezonepjt_admin.admin.jpa.UserMemberRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.data.domain.Sort;
import org.springframework.web.server.ResponseStatusException;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Slf4j
@Service
public class AdminService {

    public enum AdminPermissionRole {
        NONE("", false, false, false, false),
        USER("USER", false, false, true, false),
        LIST("LIST", true, false, false, false),
        MODIFY("MODIFY", true, true, false, false),
        MASTER("MASTER", true, true, true, true),
        USER_LIST("USER, LIST", true, false, true, false),
        USER_MODIFY("USER, MODIFY", true, true, true, false);

        private final String roleName;
        private final boolean memberList;
        private final boolean memberModify;
        private final boolean control;
        private final boolean master;

        AdminPermissionRole(
                String roleName,
                boolean memberList,
                boolean memberModify,
                boolean control,
                boolean master) {
            this.roleName = roleName;
            this.memberList = memberList;
            this.memberModify = memberModify;
            this.control = control;
            this.master = master;
        }

        public String getMemberAccess() {
            if (memberModify) {
                return "MODIFY";
            }
            return memberList ? "LIST" : "NONE";
        }

        public String getRoleName() {
            return roleName;
        }

        public boolean hasControl() {
            return control;
        }

        public boolean isMaster() {
            return master;
        }

        public List<String> toSpringRoles() {
            List<String> roles = new ArrayList<>();
            if (memberList) {
                roles.add("MEMBER_LIST");
            }
            if (memberModify) {
                roles.add("MEMBER_MODIFY");
            }
            if (control) {
                roles.add("USER");
                roles.add("CONTROL");
            }
            if (master) {
                roles.add("MASTER");
            }
            return roles;
        }

        private static AdminPermissionRole fromRoleName(String roleName) {
            if (roleName == null || roleName.isBlank() || "NONE".equalsIgnoreCase(roleName)) {
                return NONE;
            }
            if ("CONTROL".equalsIgnoreCase(roleName)) {
                return USER;
            }
            if ("LIST_CONTROL".equalsIgnoreCase(roleName)) {
                return USER_LIST;
            }
            if ("MODIFY_CONTROL".equalsIgnoreCase(roleName)) {
                return USER_MODIFY;
            }
            for (AdminPermissionRole role : values()) {
                if (role.roleName.equalsIgnoreCase(roleName.trim())) {
                    return role;
                }
            }
            throw new IllegalStateException("Unknown admin permission role: " + roleName);
        }

        private static AdminPermissionRole fromRoleNameForUpdate(String roleName) {
            if (roleName == null) {
                throw new IllegalArgumentException("Permission set is required");
            }
            String normalizedRoleName = roleName.trim().toUpperCase(java.util.Locale.ROOT);
            for (AdminPermissionRole role : values()) {
                if (role.roleName.equalsIgnoreCase(normalizedRoleName)) {
                    return role;
                }
            }
            throw new IllegalArgumentException("Invalid admin permission set: " + roleName);
        }
    }

    final public static int ADMIN_ID_ALREADY_EXIST   = 0;
    final public static int ADMIN_SIGNUP_SUCCESS     = 1;
    final public static int ADMIN_SIGNUP_FAIL        = -1;

    final public static int MODIFY_SUCCESS          = 1;
    final public static int MODIFY_FAIL             = 0;

    final public static int NEW_PASSWORD_CREATION_SUCCESS   = 1;
    final public static int NEW_PASSWORD_CREATION_FAIL      = 0;

    final private AdminDao adminDao;
    final private UserMemberRepository userMemberRepository;
    final private AuthorityRepository authorityRepository;
    final private PasswordEncoder passwordEncoder;
    final private JavaMailSender javaMailSender;
    final private AdminRepository adminRepository;
    final private AdminAuthorityRepository adminAuthorityRepository;
    final private AdminAuthorityHistoryRepository adminAuthorityHistoryRepository;
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    public AdminService(AdminDao adminDao,
                         UserMemberRepository userMemberRepository,
                         AuthorityRepository authorityRepository,
                         PasswordEncoder passwordEncoder,
                         JavaMailSender javaMailSender,
                         AdminRepository adminRepository,
                         AdminAuthorityRepository adminAuthorityRepository,
                         AdminAuthorityHistoryRepository adminAuthorityHistoryRepository) {
        this.adminDao = adminDao;
        this.userMemberRepository = userMemberRepository;
        this.authorityRepository = authorityRepository;
        this.passwordEncoder = passwordEncoder;
        this.javaMailSender = javaMailSender;
        this.adminRepository = adminRepository;
        this.adminAuthorityRepository = adminAuthorityRepository;
        this.adminAuthorityHistoryRepository = adminAuthorityHistoryRepository;
    }

    @Transactional(readOnly = true)
    public AdminPermissionRole findCurrentRole(int adminNo) {
        return latestPermissionHistory(adminNo)
                .map(history -> adminAuthorityRepository.findById(history.getAfterAuthorityNo())
                        .map(authority -> AdminPermissionRole.fromRoleName(authority.getRoleName()))
                        .orElseThrow(() -> new IllegalStateException(
                                "Authority not found: " + history.getAfterAuthorityNo())))
                .orElse(AdminPermissionRole.NONE);
    }

    @Transactional
    public boolean updatePermissions(
            int adminNo,
            String roleName,
            String changedByUsername) {
        AdminEntity changedBy = adminRepository.findByAdId(changedByUsername)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));
        if (!findCurrentRole(changedBy.getAdNo()).isMaster()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,
                    "Only a MASTER can change administrator permissions");
        }
        adminAuthorityRepository.findAllByRoleNameForUpdate("MASTER");

        AdminPermissionRole newRole;
        try {
            newRole = AdminPermissionRole.fromRoleNameForUpdate(roleName);
        } catch (IllegalArgumentException exception) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, exception.getMessage(), exception);
        }

        AdminEntity targetAdmin = adminRepository.findById(adminNo)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));

        if (targetAdmin.getAdNo() == changedBy.getAdNo()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "You cannot change your own permissions");
        }
        if (newRole.isMaster()
                && adminAuthorityHistoryRepository.existsAnotherCurrentMaster(adminNo)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "Only one administrator can have MASTER permission");
        }

        Optional<AdminAuthorityHistoryEntity> previousHistory = latestPermissionHistory(adminNo);
        AdminPermissionRole currentRole = previousHistory
                .map(history -> adminAuthorityRepository.findById(history.getAfterAuthorityNo())
                        .map(authority -> AdminPermissionRole.fromRoleName(authority.getRoleName()))
                        .orElseThrow(() -> new IllegalStateException(
                                "Authority not found: " + history.getAfterAuthorityNo())))
                .orElse(AdminPermissionRole.NONE);

        if (currentRole == newRole) {
            return false;
        }

        AdminAuthorityEntity newAuthority = adminAuthorityRepository
                .findByRoleNameIgnoreCase(newRole.getRoleName())
                .orElseGet(() -> adminAuthorityRepository.save(AdminAuthorityEntity.builder()
                        .roleName(newRole.getRoleName())
                        .build()));

        AdminAuthorityHistoryEntity history = AdminAuthorityHistoryEntity.builder()
                .adminNo(adminNo)
                .beforeAuthorityNo(previousHistory
                        .map(AdminAuthorityHistoryEntity::getAfterAuthorityNo)
                        .orElse(null))
                .afterAuthorityNo(newAuthority.getAuthorityNo())
                .changedBy(changedBy.getAdNo())
                .changedAt(LocalDateTime.now())
                .build();
        adminAuthorityHistoryRepository.save(history);
        return true;
    }

    @Transactional(readOnly = true)
    public List<AdminDto> findPermissionHistory(int adminNo, String viewerUsername) {
        AdminEntity viewer = adminRepository.findByAdId(viewerUsername)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED));
        if (!findCurrentRole(viewer.getAdNo()).isMaster()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,
                    "Only a MASTER can view administrator permission history");
        }

        AdminEntity targetAdmin = adminRepository.findById(adminNo)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        return adminAuthorityHistoryRepository.findPermissionHistory(targetAdmin.getAdNo());
    }

    private Optional<AdminAuthorityHistoryEntity> latestPermissionHistory(int adminNo) {
        return adminAuthorityHistoryRepository
                .findFirstByAdminNoOrderByChangedAtDescHistoryNoDesc(adminNo);
    }

    @Transactional
    public int signupConfirm(AdminDto adminDto) {
        log.info("signupConfirm()");

        boolean isAdmin = adminRepository.existsByAdId(adminDto.getAm_id());

        if (!isAdmin) {
            String encodedPW = passwordEncoder.encode(adminDto.getAm_pw());
            adminDto.setAm_pw(encodedPW);

            AdminEntity savedAdminEntity = adminRepository.save(adminDto.toEntity());

            if (savedAdminEntity == null) {
                return ADMIN_SIGNUP_FAIL;
            }

            AdminAuthorityEntity emptyAuthority = adminAuthorityRepository.save(
                    AdminAuthorityEntity.builder()
                            .roleName("")
                            .build());
            adminAuthorityHistoryRepository.save(AdminAuthorityHistoryEntity.builder()
                    .adminNo(savedAdminEntity.getAdNo())
                    .beforeAuthorityNo(null)
                    .afterAuthorityNo(emptyAuthority.getAuthorityNo())
                    .changedBy(savedAdminEntity.getAdNo())
                    .changedAt(LocalDateTime.now())
                    .build());
            return ADMIN_SIGNUP_SUCCESS;

        } else {
            return ADMIN_ID_ALREADY_EXIST;
        }

    }

    public String signinConfirm(AdminDto adminDto) {
        log.info("signinConfirm()");

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
        log.info("modify()");

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

    @Transactional(readOnly = true)
    public List<AdminDto> findAllAdmins() {
        log.info("findAllAdmins()");
        return adminRepository.findAll(Sort.by(Sort.Direction.DESC, "adNo"))
                .stream()
                .map(this::toManagementDto)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<UserMemberEntity> findAllUsers() {
        return userMemberRepository.findAllByOrderByUserNoDesc();
    }

    @Transactional(readOnly = true)
    public Optional<AdminDto> findAdminByNo(int adminNo) {
        return adminRepository.findById(adminNo)
                .map(this::toManagementDto);
    }

    @Transactional(readOnly = true)
    public Optional<UserMemberEntity> findUserByNo(int userNo) {
        return userMemberRepository.findByUserNo(userNo);
    }

    @Transactional
    public boolean approveUser(int userNo) {
        Optional<UserMemberEntity> optionalUser = userMemberRepository.findByUserNo(userNo);
        if (optionalUser.isEmpty()) {
            return false;
        }

        UserMemberEntity user = optionalUser.get();
        AuthorityEntity currentAuthority = user.getAuthorityEntity();
        if (currentAuthority == null
                || !"PRE_USER".equalsIgnoreCase(currentAuthority.getRoleName())) {
            return false;
        }

        AuthorityEntity approvedAuthority = authorityRepository
                .findByRoleNameIgnoreCase("APPR_USER")
                .map(authority -> {
                    authority.setRoleName("APPR_USER");
                    return authority;
                })
                .orElseGet(() -> authorityRepository.save(AuthorityEntity.builder()
                        .roleName("APPR_USER")
                        .build()));

        user.setAuthorityEntity(approvedAuthority);
        return true;
    }

    @Transactional
    public boolean deleteUser(int userNo) {
        Optional<UserMemberEntity> optionalUser = userMemberRepository.findByUserNo(userNo);
        if (optionalUser.isEmpty()) {
            return false;
        }

        userMemberRepository.deleteAuthorityLinkByUserNo(userNo);
        userMemberRepository.delete(optionalUser.get());
        return true;
    }

    @Transactional
    public boolean updateOwnAdmin(String currentUsername, AdminDto form, String currentPassword) {
        log.info("updateOwnAdmin()");
        Optional<AdminEntity> optionalAdmin = adminRepository.findByAdId(currentUsername);
        if (optionalAdmin.isEmpty()
                || isBlank(form.getAm_name())
                || isBlank(form.getAm_mail())
                || isBlank(form.getAm_phone())
                || isBlank(currentPassword)
                || !passwordEncoder.matches(currentPassword, optionalAdmin.get().getAdPw())) {
            return false;
        }

        AdminEntity admin = optionalAdmin.get();
        admin.setAdName(form.getAm_name().trim());
        admin.setAdMail(form.getAm_mail().trim());
        admin.setAdPhone(form.getAm_phone().trim());
        if (form.getAm_pw() != null && !form.getAm_pw().isBlank()) {
            admin.setAdPw(passwordEncoder.encode(form.getAm_pw()));
        }
        return true;
    }

    @Transactional
    public boolean deleteOwnAdmin(String currentUsername, String currentPassword) {
        log.info("deleteOwnAdmin()");
        Optional<AdminEntity> optionalAdmin = adminRepository.findByAdId(currentUsername);
        if (currentPassword == null || currentPassword.isBlank()
                || optionalAdmin.isEmpty()
                || !passwordEncoder.matches(currentPassword, optionalAdmin.get().getAdPw())) {
            return false;
        }
        adminRepository.delete(optionalAdmin.get());
        return true;
    }

    private AdminDto toManagementDto(AdminEntity admin) {
        log.info("toManagementDto()");
        AdminDto dto = admin.toDto();
        dto.setAm_pw(null);
        return dto;
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    @Transactional
    public int findpasswordConfirm(AdminDto adminDto) {
        log.info("findpasswordConfirm()");

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
        log.info("createNewPassword()");

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
        log.info("sendNewPasswordByMail()");

        SimpleMailMessage simpleMailMessage = new SimpleMailMessage();
        simpleMailMessage.setTo(toMailAddr);
        simpleMailMessage.setSubject("[Firezone] 새 비밀번호 안내입니다.");
        simpleMailMessage.setText("새 비밀번호: " + newPassword);

        javaMailSender.send(simpleMailMessage);

    }

}
