package com.office.firezonepjt_admin.config;

import com.office.firezonepjt_admin.admin.security.AdminAccessDeniedHandler;
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

    @Bean
    PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {

        http
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/",
                                "/admin/signin",
                                "/admin/signup",
                                "/admin/signup_confirm",
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
                                "/monitoring/**",
                                "/detection/**",
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
                );

        return http.build();
    }
}

//@Slf4j
//@Configuration
//@EnableWebSecurity
//public class SecurityConfig {
//
//    @Bean PasswordEncoder passwordEncoder() {
//        return new BCryptPasswordEncoder();
//
//    }
//
//    @Bean SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
//
//        http
//                .cors(cors -> cors.disable())
//                .csrf(csrf -> csrf.disable());
//
//        http
//                .authorizeHttpRequests(auth -> auth
//                        .requestMatchers(
//                                "/",
//                                "/css/*",
//                                "/img/*",
//                                "/js/*",
//                                "/member/signup",
//                                "/member/signup_confirm",
//                                "/member/signin",
//                                "/member/signin_confirm",
//                                "/member/findpassword",
//                                "/member/findpassword_confirm").permitAll()
//                        .requestMatchers("/planner/**").hasAnyRole("USER")
//                        .anyRequest().authenticated()
//                );
//
//        http
//                .formLogin(login -> login
//                        .loginPage("/member/signin")
//                        .loginProcessingUrl("/member/signin_confirm")
//                        .usernameParameter("id")
//                        .passwordParameter("pw")
//                        .successHandler((request, response, authentication) -> {
//                            log.info("SIGNIN SUCCESS HANDLER()");
//
//                            User user = (User) authentication.getPrincipal();
//                            String targetURI = "/member/signin_result?loginedID=" + user.getUsername();
//                            response.sendRedirect(targetURI);
//
//                        })
//                        .failureHandler((request, response, exception) -> {
//                            log.info("SIGNIN FAIL HANDLER()");
//
//                            String targetURI = "/member/signin_result";
//                            response.sendRedirect(targetURI);
//
//                        })
//                );
//
//        http
//                .logout(logout -> logout
//                        .logoutUrl("/member/signout_confirm")
//                        .logoutSuccessHandler((request, response, authentication) -> {
//                            log.info("signout success handler");
//
//                            String targetURI = "/";
//                            response.sendRedirect(targetURI);
//
//                        }));
//
//        http
//                .exceptionHandling(exception -> exception
//                        .accessDeniedHandler(new AdminAccessDeniedHandler())
//                );
//
//        return http.build();
//
//    }
//
//}
