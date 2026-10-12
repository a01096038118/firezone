package com.office.firezonepjt_user;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.persistence.autoconfigure.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication(scanBasePackages = {
        "com.office.firezonepjt_user",
        "com.office.firezonepjt.member"
})
@EntityScan(basePackages = {
        "com.office.firezonepjt.member.jpa"
})
@EnableJpaRepositories(basePackages = "com.office.firezonepjt.member.jpa")
public class FirezonePjtApplication {

    public static void main(String[] args) {
        SpringApplication.run(FirezonePjtApplication.class, args);
    }

}
