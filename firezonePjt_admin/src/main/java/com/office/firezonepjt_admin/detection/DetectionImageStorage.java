package com.office.firezonepjt_admin.detection;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.UUID;

// Flask가 보낸 탐지 이미지를 Boot 서버 폴더에 저장
// 저장 위치 : detection.image-dir (기본 uploads/detections)
// DB에는 브라우저에서 열 수 있는 주소(/uploads/detections/날짜/파일명)를 저장
@Slf4j
@Component
public class DetectionImageStorage {

    // 브라우저에서 이미지를 여는 주소의 앞부분 (WebConfig와 SecurityConfig에서도 같은 주소 사용)
    public static final String URL_PREFIX = "/uploads/detections/";

    // 허용하는 이미지 형식 -> 저장할 확장자
    private static final Map<String, String> EXTENSIONS = Map.of(
            "image/jpeg", ".jpg",
            "image/jpg", ".jpg",
            "image/png", ".png",
            "image/webp", ".webp"
    );

    private static final DateTimeFormatter DATE_DIR = DateTimeFormatter.ofPattern("yyyyMMdd");

    private final Path baseDir;

    public DetectionImageStorage(
            @Value("${detection.image-dir:uploads/detections}") String imageDir) {
        this.baseDir = Paths.get(imageDir).toAbsolutePath().normalize();
        try {
            Files.createDirectories(baseDir);
        } catch (IOException e) {
            throw new IllegalStateException("탐지 이미지 저장 폴더를 만들 수 없습니다: " + baseDir, e);
        }
        log.info("탐지 이미지 저장 폴더: {}", baseDir);
    }

    public Path getBaseDir() {
        return baseDir;
    }

    // 이미지 저장 후 DB에 넣을 주소를 반환
    public String store(MultipartFile image) {
        String contentType = image.getContentType() == null
                ? ""
                : image.getContentType().toLowerCase();
        String extension = EXTENSIONS.get(contentType);

        if (extension == null) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "이미지는 jpg, png, webp 형식만 저장할 수 있습니다."
            );
        }

        // 날짜별 폴더 + 겹치지 않는 파일명 (차량번호 등 한글은 파일명에 넣지 않음)
        String dateDir = LocalDate.now().format(DATE_DIR);
        String fileName = UUID.randomUUID() + extension;

        Path dir = baseDir.resolve(dateDir).normalize();
        Path target = dir.resolve(fileName).normalize();

        if (!target.startsWith(baseDir)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "이미지 경로가 올바르지 않습니다.");
        }

        try (InputStream in = image.getInputStream()) {
            Files.createDirectories(dir);
            Files.copy(in, target, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            log.error("탐지 이미지 저장 실패: {}", target, e);
            throw new ResponseStatusException(
                    HttpStatus.INTERNAL_SERVER_ERROR,
                    "이미지를 저장하지 못했습니다."
            );
        }

        return URL_PREFIX + dateDir + "/" + fileName;
    }

    // DB 저장에 실패했을 때 방금 저장한 이미지를 지움
    public void deleteQuietly(String imageUrl) {
        if (imageUrl == null || !imageUrl.startsWith(URL_PREFIX)) {
            return;
        }
        Path target = baseDir.resolve(imageUrl.substring(URL_PREFIX.length())).normalize();
        if (!target.startsWith(baseDir)) {
            return;
        }
        try {
            Files.deleteIfExists(target);
        } catch (IOException e) {
            log.warn("탐지 이미지 삭제 실패: {}", target, e);
        }
    }
}
