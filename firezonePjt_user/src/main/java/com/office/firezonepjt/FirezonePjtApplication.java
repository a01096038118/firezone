package com.office.firezonepjt;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.persistence.autoconfigure.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@SpringBootApplication(scanBasePackages = {
        "com.office.firezonepjt.user",
        "com.office.firezonepjt.config"
})

@EntityScan(basePackages = {
        "com.office.firezonepjt.user.jpa"
})
@EnableJpaRepositories(basePackages = "com.office.firezonepjt.user.jpa")
public class FirezonePjtApplication {

    public static void main(String[] args) {
        SpringApplication.run(FirezonePjtApplication.class, args);
    }

}
