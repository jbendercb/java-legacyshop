package com.example.legacyshop.exception;

/**
 * Exception thrown when trying to create a resource that already exists.
 * Maps to HTTP 409 Conflict.
 */
public class DuplicateResourceException extends RuntimeException {
    
    public DuplicateResourceException(String message) {
        super(message);
    }
    
    public DuplicateResourceException(String message, Throwable cause) {
        super(message, cause);
    }
}