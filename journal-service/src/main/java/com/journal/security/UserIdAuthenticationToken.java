package com.journal.security;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Collections;

public class UserIdAuthenticationToken extends AbstractAuthenticationToken {

    private final String userId;

    public UserIdAuthenticationToken(String userId) {
        super(Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER")));
        this.userId = userId;
        setAuthenticated(true);
    }

    @Override
    public Object getCredentials() {
        return null;
    }

    @Override
    public Object getPrincipal() {
        return new UserDetailsAdapter(userId);
    }

    public String getUserId() {
        return userId;
    }
}
