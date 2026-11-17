package com.office.firezonepjt.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

// 대시보드 화면(common.js)에 Flask 서버 주소와 admin 서버 주소를 넘겨줌
// 현장마다 바뀌는 주소를 코드 대신 설정(환경변수 DASHBOARD_FLASKBASEURL, DASHBOARD_ADMINBASEURL)으로 바꿀 수 있게 함
@ControllerAdvice
public class DashboardUrlAdvice {

    private final String flaskBaseUrl;
    private final String adminBaseUrl;

    public DashboardUrlAdvice(
            @Value("${dashboard.flask-base-url:http://192.168.0.106:5000}") String flaskBaseUrl,
            @Value("${dashboard.admin-base-url:http://192.168.56.103:8090}") String adminBaseUrl) {
        this.flaskBaseUrl = flaskBaseUrl;
        this.adminBaseUrl = adminBaseUrl;
    }

    @ModelAttribute("flaskBaseUrl")
    public String flaskBaseUrl() {
        return flaskBaseUrl;
    }

    @ModelAttribute("adminBaseUrl")
    public String adminBaseUrl() {
        return adminBaseUrl;
    }
}
