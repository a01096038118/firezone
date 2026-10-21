package com.office.firezonepjt_admin.admin;

import com.office.firezonepjt_admin.admin.jpa.UserMemberEntity;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Slf4j
@Controller
@RequestMapping("/admin")
public class AdminController {

    final private AdminService adminService;

    public AdminController(AdminService adminService) {
        this.adminService = adminService;
    }

    // 회원가입 양식
    @GetMapping("/signup")
    public String signup() {
        log.info("signup()");

        String nextPage = "admin/signup_form";

        return nextPage;

    }

    // 회원가입 확인
    @PostMapping("/signup_confirm")
    public String signupConfirm(AdminDto adminDto, Model model) {
        log.info("signupConfirm()");

        String nextPage = "admin/signup_result";

        int result = adminService.signupConfirm(adminDto);
        model.addAttribute("result", result);

        return nextPage;

    }

    // 로그인 양식 /signin
    @GetMapping("/signin")
    public String signin(
            @RequestParam(value = "deleted", required = false) String deleted,
            Model model) {
        log.info("signin()");

        model.addAttribute("accountDeleted", deleted != null);
        String nextPage = "admin/signin_form";

        return nextPage;

    }

    @GetMapping("/members_list")
    public String membersList(Model model) {
        log.info("membersList()");
        model.addAttribute("admins", adminService.findAllAdmins());
        model.addAttribute("users", adminService.findAllUsers());

        String nextPage = "admin/members";

        return nextPage;
    }

    @GetMapping("/members_list/admin/{adminNo}")
    public String adminMemberDetail(@PathVariable int adminNo, Model model) {

        AdminDto findAdminOr404 = adminService.findAdminByNo(adminNo)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));

        model.addAttribute("admin", findAdminOr404);

        String nextPage = "admin/admin_member_detail";

        return nextPage;
    }

    @GetMapping("/members_list/user/{userNo}")
    public String userMemberDetail(@PathVariable int userNo, Model model) {

        UserMemberEntity user = adminService.findUserByNo(userNo)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));

        model.addAttribute("user", user);

        String nextPage = "admin/user_member_detail";

        return nextPage;
    }

    @PostMapping("/members_list/user/{userNo}/approve")
    public String approveUser(
            @PathVariable int userNo,
            RedirectAttributes redirectAttributes) {
        if (!adminService.approveUser(userNo)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage", "회원이 없거나 이미 승인된 계정입니다.");
        } else {
            redirectAttributes.addFlashAttribute("message", "일반 회원을 승인했습니다.");
        }
        return "redirect:/admin/members_list/user/" + userNo;
    }

    @PostMapping("/members_list/user/{userNo}/delete")
    public String deleteUser(
            @PathVariable int userNo,
            RedirectAttributes redirectAttributes) {
        if (!adminService.deleteUser(userNo)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage", "삭제할 회원이 이미 존재하지 않습니다.");
            return "redirect:/admin/members_list";
        }

        redirectAttributes.addFlashAttribute("message", "일반 회원을 삭제했습니다.");
        return "redirect:/admin/members_list";
    }

    // 비밀번호 찾기 양식(/member/findpassword)
    @GetMapping({"/findpassword"})
    public String findpassword(AdminDto adminDto, Model model) {
        log.info("findpassword()");

        String nextPage = "admin/findpassword_form";

        return nextPage;

    }

    // 비밀번호 찾기 확인(/member/findpassword_confirm)
    @PostMapping({"/findpassword_confirm"})
    public String findpasswordConfirm(AdminDto adminDto, Model model) {
        log.info("findpasswordConfirm()");

        String nextPage = "admin/findpassword_result";

        int result = adminService.findpasswordConfirm(adminDto);
        model.addAttribute("result", result);

        return nextPage;

    }

    @GetMapping("/signin_result")
    public String signinResult(
            @RequestParam(value = "loginedID", required = false) String loginedID,
            @RequestParam(value = "error", required = false) String error,
            Model model) {
        log.info("signinResult()");

        String nextPage = "admin/signin_result";
        model.addAttribute("loginedID", loginedID);
        model.addAttribute("loginError", error != null);

        return nextPage;

    }

    // 권한이 없어서 접근이 막힌경우(/admin/access_denied)
    @GetMapping("/access_denied")
    public String accessDenied() {
        log.info("accessDenied()");

        String nextPage = "admin/access_denied";

        return nextPage;

    }

    @GetMapping({"/myinfocheck", "/modify"})
    public String myinfocheck(Authentication authentication, Model model) {
        log.info("myinfocheck()");

        AdminDto admin = adminService.modify(authentication.getName());
        if (admin == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
        admin.setAm_pw(null);
        model.addAttribute("admin", admin);
        return "admin/myinfocheck";
    }

    @PostMapping({"/myinfocheck", "/modify_confirm"})
    public String updateMyInfo(
            AdminDto form,
            @RequestParam("currentPassword") String currentPassword,
            Authentication authentication,
            RedirectAttributes redirectAttributes) {
        String password = form.getAm_pw();
        if (isBlank(form.getAm_name())
                || isBlank(form.getAm_mail())
                || isBlank(form.getAm_phone())
                || isBlank(currentPassword)
                || form.getAm_name().trim().length() > 20
                || form.getAm_mail().trim().length() > 20
                || form.getAm_phone().trim().length() > 20
                || (password != null && !password.isBlank() && password.length() < 8)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage",
                    "현재 비밀번호와 이름, 이메일, 전화번호를 입력해 주세요(각 20자 이하). 새 비밀번호는 입력할 경우 8자 이상이어야 합니다.");
            return "redirect:/admin/myinfocheck";
        }
        if (!adminService.updateOwnAdmin(authentication.getName(), form, currentPassword)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage", "현재 비밀번호가 올바르지 않습니다. 변경 사항을 저장하지 않았습니다.");
            return "redirect:/admin/myinfocheck";
        }
        redirectAttributes.addFlashAttribute("message", "내 정보를 수정했습니다.");
        return "redirect:/admin/myinfocheck";
    }

    @PostMapping("/myinfocheck/delete")
    public String deleteMyInfo(
            @RequestParam("currentPassword") String currentPassword,
            Authentication authentication,
            HttpServletRequest request,
            RedirectAttributes redirectAttributes) {
        if (!adminService.deleteOwnAdmin(authentication.getName(), currentPassword)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage", "현재 비밀번호가 올바르지 않습니다. 탈퇴하지 않았습니다.");
            return "redirect:/admin/myinfocheck";
        }
        if (request.getSession(false) != null) {
            request.getSession(false).invalidate();
        }
        return "redirect:/admin/signin?deleted";
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

}
