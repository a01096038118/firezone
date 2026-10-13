package com.office.firezonepjt_admin.admin;

import jakarta.servlet.http.HttpSession;
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
    public String signin() {
        log.info("signin()");

        String nextPage = "admin/signin_form";

        return nextPage;

    }

    // 계정 수정 양식(/member/modify)
    @GetMapping("/modify")
    public String modify(HttpSession session, Model model) {
        log.info("modify()");

        String nextPage = "admin/modify_form";

        String loginedID = String.valueOf(session.getAttribute("loginedID"));
        AdminDto loginedAdminDto = adminService.modify(loginedID);
        model.addAttribute("loginedAdminDto", loginedAdminDto);

        return nextPage;

    }

    @GetMapping("/members")
    public String members(Model model) {
        model.addAttribute("admins", adminService.findAllAdmins());
        return "admin/members";
    }

    @GetMapping("/members/{adminNo}")
    public String memberDetail(@PathVariable int adminNo, Model model) {
        model.addAttribute("admin", findAdminOr404(adminNo));
        return "admin/member_detail";
    }

    @GetMapping("/members/{adminNo}/edit")
    public String editMember(@PathVariable int adminNo, Model model) {
        model.addAttribute("admin", findAdminOr404(adminNo));
        return "admin/member_edit_form";
    }

    @PostMapping("/members/{adminNo}/edit")
    public String updateMember(
            @PathVariable int adminNo,
            AdminDto form,
            Model model,
            RedirectAttributes redirectAttributes) {
        AdminDto existingAdmin = findAdminOr404(adminNo);
        String password = form.getAm_pw();
        if (isBlank(form.getAm_name())
                || isBlank(form.getAm_mail())
                || isBlank(form.getAm_phone())
                || form.getAm_name().trim().length() > 20
                || form.getAm_mail().trim().length() > 20
                || form.getAm_phone().trim().length() > 20
                || (password != null && !password.isBlank() && password.length() < 8)) {
            form.setAm_no(existingAdmin.getAm_no());
            form.setAm_id(existingAdmin.getAm_id());
            form.setAm_reg_date(existingAdmin.getAm_reg_date());
            form.setAm_mod_date(existingAdmin.getAm_mod_date());
            form.setAm_pw(null);
            model.addAttribute("admin", form);
            model.addAttribute(
                    "errorMessage",
                    "이름, 이메일, 전화번호를 입력해 주세요(각 20자 이하). 새 비밀번호는 입력할 경우 8자 이상이어야 합니다.");
            return "admin/member_edit_form";
        }

        if (!adminService.updateAdmin(adminNo, form)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
        redirectAttributes.addFlashAttribute("message", "회원 정보를 수정했습니다.");
        return "redirect:/admin/members/" + adminNo;
    }

    @PostMapping("/members/{adminNo}/delete")
    public String deleteMember(
            @PathVariable int adminNo,
            Authentication authentication,
            RedirectAttributes redirectAttributes) {
        boolean deleted = adminService.deleteAdmin(adminNo, authentication.getName());
        if (!deleted) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage", "현재 로그인한 관리자이거나 이미 존재하지 않는 계정은 삭제할 수 없습니다.");
            return "redirect:/admin/members";
        }

        redirectAttributes.addFlashAttribute("message", "회원 계정을 삭제했습니다.");
        return "redirect:/admin/members";
    }

    private AdminDto findAdminOr404(int adminNo) {
        return adminService.findAdminByNo(adminNo)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    // 계정 수정 확인(/member/modify_confirm)
    @PostMapping("/modify_confirm")
    public String modifyConfirm(AdminDto adminDto, Model model) {
        log.info("modifyConfirm()");

        String nextPage = "admin/modify_result";

        int result = adminService.modifyConfirm(adminDto);
        model.addAttribute("result", result);

        return nextPage;

    }

    // 비밀번호 찾기 양식(/member/findpassword)
    @GetMapping("/findpassword")
    public String findpassword(AdminDto adminDto, Model model) {
        log.info("findpassword()");

        String nextPage = "admin/findpassword_form";

        return nextPage;

    }

    // 비밀번호 찾기 확인(/member/findpassword_confirm)
    @PostMapping("/findpassword_confirm")
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

}
