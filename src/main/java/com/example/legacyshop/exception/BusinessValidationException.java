package com.example.legacyshop.exception;

/**
 * Exception thrown when business validation fails.
 * Maps to HTTP 400 Bad Request.
 */
public class BusinessValidationException extends RuntimeException {
    
    public BusinessValidationException(String message) {
        super(message);
    }
    
    public BusinessValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}