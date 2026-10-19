package com.office.firezonepjt.detection;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestControllerAdvice(basePackageClasses = DetectionController.class)
public class DetectionExceptionHandler {

    // 서비스에서 던진 오류 (404, 400 등)
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Map<String, String>> handleStatus(ResponseStatusException e) {
        return ResponseEntity.status(e.getStatusCode())
                .body(Map.of("message", e.getReason() != null ? e.getReason() : "요청을 처리할 수 없습니다."));
    }

    // 파라미터 누락·형식 오류 (예: dl_no 없음, 날짜 형식 틀림)
    @ExceptionHandler({
            MissingServletRequestParameterException.class,
            MethodArgumentTypeMismatchException.class
    })
    public ResponseEntity<Map<String, String>> handleBadParam(Exception e) {
        return ResponseEntity.badRequest()
                .body(Map.of("message", "요청 파라미터가 올바르지 않습니다."));
    }
}

