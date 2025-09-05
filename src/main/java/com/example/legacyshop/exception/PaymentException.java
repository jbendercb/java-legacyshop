package com.example.legacyshop.exception;

/**
 * Exception thrown when payment processing fails.
 * Maps to HTTP 502 Bad Gateway when external service fails.
 */
public class PaymentException extends RuntimeException {
    
    private final boolean retryable;
    
    public PaymentException(String message, boolean retryable) {
        super(message);
        this.retryable = retryable;
    }
    
    public PaymentException(String message, Throwable cause, boolean retryable) {
        super(message, cause);
        this.retryable = retryable;
    }
    
    public boolean isRetryable() {
        return retryable;
    }
}