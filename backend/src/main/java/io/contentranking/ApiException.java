package io.contentranking;

import org.springframework.http.HttpStatus;

class ApiException extends RuntimeException {
    final HttpStatus status;
    final String code;

    private ApiException(HttpStatus status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }

    static ApiException invalid(String message) {
        return new ApiException(HttpStatus.BAD_REQUEST, "INVALID_REQUEST", message);
    }

    static ApiException missing(String message) {
        return new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", message);
    }

    static ApiException conflict(String message) {
        return new ApiException(HttpStatus.CONFLICT, "REVIEW_CONFLICT", message);
    }
}
