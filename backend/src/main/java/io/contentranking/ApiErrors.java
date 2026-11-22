package io.contentranking;

import jakarta.validation.ConstraintViolationException;
import java.util.UUID;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

@RestControllerAdvice
class ApiErrors {
    record ErrorBody(String code, String message, String correlationId) {}

    @ExceptionHandler(ApiException.class)
    ResponseEntity<ErrorBody> domain(ApiException error) {
        return error(error.status, error.code, error.getMessage());
    }

    @ExceptionHandler({HttpMessageNotReadableException.class, MethodArgumentNotValidException.class,
        MethodArgumentTypeMismatchException.class, ConstraintViolationException.class,
        MissingRequestHeaderException.class, HandlerMethodValidationException.class})
    ResponseEntity<ErrorBody> validation(Exception error) {
        return error(HttpStatus.BAD_REQUEST, "INVALID_REQUEST", "Check request fields and headers.");
    }

    @ExceptionHandler(DataAccessException.class)
    ResponseEntity<ErrorBody> dataAccess(DataAccessException error) {
        return error(HttpStatus.SERVICE_UNAVAILABLE, "DATA_UNAVAILABLE", "The ranking database is unavailable.");
    }

    private ResponseEntity<ErrorBody> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status).body(new ErrorBody(code, message, UUID.randomUUID().toString()));
    }
}
