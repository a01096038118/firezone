package com.office.firezonepjt_admin.admin.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

public class AdminPermissionRefreshFilter extends OncePerRequestFilter {

    private final AdminDetailsService adminDetailsService;

    public AdminPermissionRefreshFilter(AdminDetailsService adminDetailsService) {
        this.adminDetailsService = adminDetailsService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null
                && authentication.isAuthenticated()
                && !(authentication instanceof AnonymousAuthenticationToken)) {
            try {
                UserDetails currentUser =
                        adminDetailsService.loadUserByUsername(authentication.getName());
                UsernamePasswordAuthenticationToken refreshedAuthentication =
                        UsernamePasswordAuthenticationToken.authenticated(
                                currentUser,
                                null,
                                currentUser.getAuthorities());
                refreshedAuthentication.setDetails(authentication.getDetails());
                SecurityContextHolder.getContext().setAuthentication(refreshedAuthentication);
            } catch (UsernameNotFoundException exception) {
                SecurityContextHolder.clearContext();
                var session = request.getSession(false);
                if (session != null) {
                    session.invalidate();
                }
                response.sendRedirect(request.getContextPath() + "/admin/signin?deleted");
                return;
            }
        }

        filterChain.doFilter(request, response);
    }
}
