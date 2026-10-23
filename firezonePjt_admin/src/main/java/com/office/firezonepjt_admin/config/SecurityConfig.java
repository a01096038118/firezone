package com.office.firezonepjt_admin.config;

import com.office.firezonepjt_admin.admin.security.AdminDetailsService;
import com.office.firezonepjt_admin.admin.security.AdminPermissionRefreshFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.access.intercept.AuthorizationFilter;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http, AdminDetailsService adminDetailsService) throws Exception {

        http
                // Flask의 탐지 저장 요청 -> 로그인 토큰이 없으므로 경로 제외
                .csrf(csrf -> csrf
                        .ignoringRequestMatchers("/detections")
                )
                .authorizeHttpRequests(auth -> auth
                        // Flask 탐지 저장 :  로그인 없이 통과
                        .requestMatchers(HttpMethod.POST, "/detections").permitAll()
                        // 탐지 삭제 : MASTER만 (/detections/** 규칙보다 반드시 위에 있어야 함)
                        .requestMatchers(HttpMethod.DELETE, "/detections/delete")
                        .hasRole("MASTER")
                        // CSV 다운로드 : MODIFY 이상 (MASTER도 MODIFY를 가짐)
                        .requestMatchers(HttpMethod.GET, "/detections/csv")
                        .hasRole("MODIFY")
                        // 관리자 권한 변경 / 권한 이력 조회 : MASTER만
                        .requestMatchers(HttpMethod.POST, "/admin/members_list/admin/*/authority")
                        .hasRole("MASTER")
                        .requestMatchers(HttpMethod.GET, "/admin/members_list/admin/*/authority-history")
                        .hasRole("MASTER")
                        .requestMatchers(HttpMethod.POST, "/admin/members_list/user/**")
                        .hasRole("MODIFY")
                        .requestMatchers(
                                "/admin/members_list",
                                "/admin/members_list/admin/**"
                        ).hasAnyRole("CONTROL", "MODIFY", "MASTER")
                        .requestMatchers("/admin/members_list/user/**")
                        .hasAnyRole("CONTROL", "MODIFY", "MASTER")
                        .requestMatchers("/dashboard/**", "/detections/**", "/uploads/detections/**")
                        .hasAnyRole("CONTROL", "MASTER")
                        .requestMatchers(
                                "/",
                                "/admin/signin",
                                "/admin/signup",
                                "/admin/signup_confirm",
                                "/admin/id-check",
                                "/admin/findpassword",
                                "/admin/findpassword_confirm",
                                "/admin/signin_result",
                                "/admin/access_denied",
                                "/css/**",
                                "/js/**",
                                "/img/**",
                                "/include/**"
                        ).permitAll()
                        .requestMatchers(
                                "/admin/**",
                                "/planner/**",
                                "/logs/**"
                        ).hasRole("ADMIN")
                        .anyRequest().permitAll()
                )
                .formLogin(form -> form
                        .loginPage("/admin/signin")
                        .loginProcessingUrl("/admin/signin_confirm")
                        .usernameParameter("am_id")
                        .passwordParameter("am_pw")
                        .defaultSuccessUrl("/", true)
                        .failureUrl("/admin/signin_result?error")
                        .permitAll()
                )
                .logout(logout -> logout
                        .logoutUrl("/admin/logout")
                        .logoutSuccessUrl("/admin/signin?logout")
                        .permitAll()
                )
                .addFilterBefore(
                        new AdminPermissionRefreshFilter(adminDetailsService),
                        AuthorizationFilter.class);

        return http.build();
    }
}
