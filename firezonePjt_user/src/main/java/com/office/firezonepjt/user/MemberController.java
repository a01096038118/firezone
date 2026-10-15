package com.office.firezonepjt.user;

import jakarta.servlet.http.HttpSession;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.security.Principal;

@Slf4j
@Controller
@RequestMapping("/member")
public class MemberController {

    final private String CLASS_NAME = "[MemberController] ";

    final private MemberService memberService;

    public MemberController(MemberService memberService) {
        this.memberService = memberService;
    }

    // 회원가입 양식
    @GetMapping("/signup")
    public String signup() {
        System.out.println(CLASS_NAME.concat("signup()"));

        String nextPage = "member/signup_form";

        return nextPage;

    }

    // 회원가입 확인
    @PostMapping("/signup_confirm")
    public String signupConfirm(MemberDto memberDto, Model model) {
        System.out.println(CLASS_NAME.concat("signupConfirm()"));

        String nextPage = "member/signup_result";

        int result = memberService.signupConfirm(memberDto);
        model.addAttribute("result", result);

        return nextPage;

    }

    // 로그인 양식 /signin
    @GetMapping("/signin")
    public String signin(
            @RequestParam(value = "withdrawn", required = false) String withdrawn,
            Model model) {
        System.out.println(CLASS_NAME.concat("signin()"));

        model.addAttribute("accountWithdrawn", withdrawn != null);
        String nextPage = "member/signin_form";

        return nextPage;

    }

//    로그인 확인 /signin_confirm

    @PostMapping("/signin_confirm")
    public String signinConfirm(MemberDto memberDto,
                                Model model,
                                HttpSession session) {
        System.out.println(CLASS_NAME.concat("signinConfirm()"));

        String nextPage = "member/signin_result";

        String loginedID = memberService.signinConfirm(memberDto);
        model.addAttribute("loginedID", loginedID);

        if (loginedID != null) {
            session.setAttribute("loginedID", loginedID);
            session.setMaxInactiveInterval(60 * 30);
        }

        return nextPage;

    }

    // 로그 아웃 /signout_confirm
    /*
    @GetMapping("/signout_confirm")
    public String signoutConfirm(HttpSession session) {
        System.out.println(CLASS_NAME.concat("signoutConfirm()"));

        String nextPage = "redirect:/";

        session.invalidate();

        return nextPage;

    }
    */

    // 계정 수정 양식(/member/modify)
    @GetMapping("/modify")
    public String modify(Principal principal, Model model) {
        System.out.println(CLASS_NAME.concat("modify()"));

        String nextPage = "member/modify_form";

        MemberDto loginedMemberDto = memberService.modify(principal.getName());
        model.addAttribute("loginedMemberDto", loginedMemberDto);

        return nextPage;

    }

    @PostMapping("/withdraw")
    public String withdraw(
            @RequestParam("currentPassword") String currentPassword,
            Principal principal,
            HttpSession session,
            RedirectAttributes redirectAttributes) {
        if (!memberService.withdraw(principal.getName(), currentPassword)) {
            redirectAttributes.addFlashAttribute(
                    "errorMessage", "현재 비밀번호가 올바르지 않습니다. 탈퇴하지 않았습니다.");
            return "redirect:/member/modify";
        }

        session.invalidate();
        return "redirect:/member/signin?withdrawn";
    }

    // 계정 수정 확인(/member/modify_confirm)
    @PostMapping("/modify_confirm")
    public String modifyConfirm(MemberDto memberDto, Principal principal, Model model) {
        System.out.println(CLASS_NAME.concat("modifyConfirm()"));

        String nextPage = "member/modify_result";

        int result = memberService.modifyConfirm(principal.getName(), memberDto);
        model.addAttribute("result", result);

        return nextPage;

    }

    // 비밀번호 찾기 양식(/member/findpassword)
    @GetMapping({"/findpassword"})
    public String findpassword(MemberDto memberDto, Model model) {
        System.out.println(CLASS_NAME.concat("findpassword()"));

        String nextPage = "member/findpassword_form";

        return nextPage;

    }

    // 비밀번호 찾기 확인(/member/findpassword_confirm)
    @PostMapping({"/findpassword_confirm"})
    public String findpasswordConfirm(MemberDto memberDto, Model model) {
        System.out.println(CLASS_NAME.concat("findpasswordConfirm()"));

        String nextPage = "member/findpassword_result";

        int result = memberService.findpasswordConfirm(memberDto);
        model.addAttribute("result", result);

        return nextPage;

    }

    @GetMapping("/signin_result")
    public String signinResult(
            @RequestParam(value = "loginedID", required = false) String loginedID,
            @RequestParam(value = "error", required = false) String error,
            Model model) {
        log.info("signinResult");

        String nextPage = "member/signin_result";
        model.addAttribute("loginedID", loginedID);
        model.addAttribute("approvalPending", "approval_pending".equalsIgnoreCase(error));
        model.addAttribute("loginFailed", error != null);

        return nextPage;

    }

    // 권한이 없어서 접근이 막힌경우(/member/access_denied)
    @GetMapping("/access_denied")
    public String accessDenied() {
        log.info("accessDenied()");

        String nextPage = "member/access_denied";

        return nextPage;

    }

}
