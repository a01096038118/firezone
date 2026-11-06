package com.office.firezonepjt_admin.detection.jpa;

import com.office.firezonepjt_admin.detection.DetectionController;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;
import java.util.stream.Collectors;

@RestControllerAdvice(basePackageClasses = DetectionController.class)
public class DetectionExceptionHandler {

    // @Valid 검증 실패(필수값 누락, 길이 초과 등)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidation(
            MethodArgumentNotValidException e) {

        String message = e.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.joining(","));

        return error(HttpStatus.BAD_REQUEST,
                message.isBlank() ? "요청 값이 올바르지 않습니다." : message);
    }

    // 필수 파라미터 누락, 파라미터 형식 오류 (dl_no에 문자, 날짜 형식 오류 등)
    @ExceptionHandler({MissingServletRequestParameterException.class,
    MethodArgumentTypeMismatchException.class})
    public ResponseEntity<Map<String, String>> handleParameter(Exception e) {
        return error(HttpStatus.BAD_REQUEST, "요청 파라미터가 올바르지 않습니다.");
    }

    // 서비스에 던진 ResponseStatusException
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Map<String, String>> handleStatus(
            ResponseStatusException e){

        String message = e.getReason() != null
                ? e.getReason()
                : "요청을 처리할 수 없습니다.";

        return ResponseEntity.status(e.getStatusCode())
                .body(Map.of("message", message));
    }

    private ResponseEntity<Map<String, String>> error(HttpStatus status, String message){
        return ResponseEntity.status(status).body(Map.of("message", message));
    }


}
