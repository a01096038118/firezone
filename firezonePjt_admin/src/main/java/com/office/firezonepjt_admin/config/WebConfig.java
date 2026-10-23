package com.office.firezonepjt_admin.config;

import com.office.firezonepjt_admin.detection.DetectionImageStorage;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final DetectionImageStorage detectionImageStorage;

    public WebConfig(DetectionImageStorage detectionImageStorage) {
        this.detectionImageStorage = detectionImageStorage;
    }

    // 저장된 탐지 이미지를 /uploads/detections/** 주소로 열 수 있게 연결
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        String location = detectionImageStorage.getBaseDir().toUri().toString();
        if (!location.endsWith("/")) {
            location += "/";
        }
        registry.addResourceHandler(DetectionImageStorage.URL_PREFIX + "**")
                .addResourceLocations(location);
    }
}
