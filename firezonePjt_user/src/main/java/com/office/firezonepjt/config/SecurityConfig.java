package com.office.firezonepjt.config;

import com.office.firezonepjt.user.security.MemberAccessDeniedHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Slf4j
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();

    }

    @Bean SecurityFilterChain filterChain(HttpSecurity http) throws Exception {

        http
                .cors(cors -> cors.disable())
                .csrf(csrf -> csrf.disable());

        http
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/",
                                "/error",
                                "/favicon.ico",
                                "/css/**",
                                "/img/**",
                                "/js/**",
                                "/include/**",
                                "/member/signup",
                                "/member/signup_confirm",
                                "/member/signin",
                                "/member/signin_confirm",
                                "/member/signin_result",
                                "/member/findpassword",
                                "/member/findpassword_confirm",
                                "/member/access_denied").permitAll()
                        .requestMatchers("/planner/**").hasAnyRole("USER")
                        .anyRequest().authenticated()
                );

        http
                .formLogin(login -> login
                        .loginPage("/member/signin")
                        .loginProcessingUrl("/member/signin_confirm")
                        .usernameParameter("um_id")
                        .passwordParameter("um_pw")
                        .successHandler((request, response, authentication) -> {
                            log.info("SIGNIN SUCCESS HANDLER()");

                            String targetURI = request.getContextPath()
                                    + "/member/signin_result?loginedID="
                                    + java.net.URLEncoder.encode(
                                            authentication.getName(),
                                            java.nio.charset.StandardCharsets.UTF_8);
                            response.sendRedirect(targetURI);

                        })
                        .failureHandler((request, response, exception) -> {
                            log.info("SIGNIN FAIL HANDLER()");

                            String targetURI = request.getContextPath() + "/member/signin_result";
                            response.sendRedirect(targetURI);

                        })
                );

        http
                .logout(logout -> logout
                        .logoutUrl("/member/signout_confirm")
                        .logoutSuccessHandler((request, response, authentication) -> {
                            log.info("signout success handler");

                            String targetURI = "/";
                            response.sendRedirect(targetURI);

                        }));

        http
                .exceptionHandling(exception -> exception
                        .accessDeniedHandler(new MemberAccessDeniedHandler())
                );

        return http.build();

    }

}
