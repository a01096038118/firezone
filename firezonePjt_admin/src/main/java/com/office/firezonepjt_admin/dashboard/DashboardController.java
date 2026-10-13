package com.office.firezonepjt_admin.dashboard;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Slf4j
@Controller
@RequestMapping("/dashboard")
public class DashboardController {

    // 실시간 관제 화면
    @GetMapping("/monitoring")
    public String monitoring() {
        log.info("monitoring()");

        String nextPage = "dashboard/monitoring";

        return nextPage;
    }

    // 탐지 목록
    @GetMapping("/detection")
    public String detection() {
        log.info("detection()");

        String nextPage = "list_detail";

        return nextPage;
    }

    // 탐지 목록 상세
    @GetMapping("/listDetail")
    public String listDetail() {
        log.info("list_detail()");

        String nextPage = "dashboard/list_detail";

        return nextPage;
    }

    // 로그 목록
    @GetMapping("/logList")
    public String logList() {
        log.info("log_list()");

        String nextPage = "dashboard/log_list";

        return nextPage;
    }

    // 로그 목록 상세
    @GetMapping("/logDetail")
    public String logDetail() {
        log.info("logDetail()");

        String nextPage = "dashboard/log_detail";

        return nextPage;
    }


}
