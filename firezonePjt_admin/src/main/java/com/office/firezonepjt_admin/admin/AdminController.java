package com.office.firezonepjt_admin.admin;

import jakarta.servlet.http.HttpSession;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

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
            Model model) {
        log.info("signinResult");

        String nextPage = "admin/signin_result";
        model.addAttribute("loginedID", loginedID);

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
