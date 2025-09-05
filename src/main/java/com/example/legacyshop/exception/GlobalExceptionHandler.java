package com.example.legacyshop.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;
import java.util.HashMap;
import java.util.Map;

/**
 * Global exception handler that produces RFC-7807 Problem Details responses.
 * 
 * Spring Boot 3 has built-in Problem Details support enabled via:
 * spring.mvc.problemdetails.enabled=true
 * 
 * This handler customizes the Problem Details for business exceptions:
 * - 400 Bad Request for validation/business rule violations
 * - 404 Not Found for resource not found
 * - 409 Conflict for duplicate resources
 * - 502 Bad Gateway for external service failures
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * Handle validation errors (400 Bad Request).
     * Maps Spring validation errors to Problem Details format.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidationException(MethodArgumentNotValidException ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problemDetail.setTitle("Validation Failed");
        problemDetail.setDetail("One or more fields have invalid values");
        problemDetail.setType(URI.create("/problems/validation-error"));
        
        // Add field-specific errors
        Map<String, String> fieldErrors = new HashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            fieldErrors.put(error.getField(), error.getDefaultMessage());
        }
        problemDetail.setProperty("fieldErrors", fieldErrors);
        
        logger.warn("Validation error: {}", fieldErrors);
        return ResponseEntity.badRequest().body(problemDetail);
    }

    /**
     * Handle business validation errors (400 Bad Request).
     */
    @ExceptionHandler(BusinessValidationException.class)
    public ResponseEntity<ProblemDetail> handleBusinessValidationException(BusinessValidationException ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problemDetail.setTitle("Business Rule Violation");
        problemDetail.setDetail(ex.getMessage());
        problemDetail.setType(URI.create("/problems/business-validation-error"));
        
        logger.warn("Business validation error: {}", ex.getMessage());
        return ResponseEntity.badRequest().body(problemDetail);
    }

    /**
     * Handle resource not found errors (404 Not Found).
     */
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleResourceNotFoundException(ResourceNotFoundException ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        problemDetail.setTitle("Resource Not Found");
        problemDetail.setDetail(ex.getMessage());
        problemDetail.setType(URI.create("/problems/resource-not-found"));
        
        logger.warn("Resource not found: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(problemDetail);
    }

    /**
     * Handle duplicate resource errors (409 Conflict).
     */
    @ExceptionHandler(DuplicateResourceException.class)
    public ResponseEntity<ProblemDetail> handleDuplicateResourceException(DuplicateResourceException ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.CONFLICT);
        problemDetail.setTitle("Resource Already Exists");
        problemDetail.setDetail(ex.getMessage());
        problemDetail.setType(URI.create("/problems/duplicate-resource"));
        
        logger.warn("Duplicate resource error: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT).body(problemDetail);
    }

    /**
     * Handle payment service errors (502 Bad Gateway).
     * Maps external service failures to appropriate HTTP status.
     */
    @ExceptionHandler(PaymentException.class)
    public ResponseEntity<ProblemDetail> handlePaymentException(PaymentException ex) {
        HttpStatus status = ex.isRetryable() ? HttpStatus.BAD_GATEWAY : HttpStatus.BAD_REQUEST;
        
        ProblemDetail problemDetail = ProblemDetail.forStatus(status);
        problemDetail.setTitle(ex.isRetryable() ? "External Service Unavailable" : "Payment Failed");
        problemDetail.setDetail(ex.getMessage());
        problemDetail.setType(URI.create("/problems/payment-error"));
        problemDetail.setProperty("retryable", ex.isRetryable());
        
        if (ex.isRetryable()) {
            logger.error("Payment service error (retryable): {}", ex.getMessage());
        } else {
            logger.warn("Payment error (not retryable): {}", ex.getMessage());
        }
        
        return ResponseEntity.status(status).body(problemDetail);
    }

    /**
     * Handle general illegal state errors (400 Bad Request).
     */
    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<ProblemDetail> handleIllegalStateException(IllegalStateException ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problemDetail.setTitle("Invalid State");
        problemDetail.setDetail(ex.getMessage());
        problemDetail.setType(URI.create("/problems/invalid-state"));
        
        logger.warn("Illegal state error: {}", ex.getMessage());
        return ResponseEntity.badRequest().body(problemDetail);
    }

    /**
     * Handle illegal argument errors (400 Bad Request).
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ProblemDetail> handleIllegalArgumentException(IllegalArgumentException ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problemDetail.setTitle("Invalid Argument");
        problemDetail.setDetail(ex.getMessage());
        problemDetail.setType(URI.create("/problems/invalid-argument"));
        
        logger.warn("Illegal argument error: {}", ex.getMessage());
        return ResponseEntity.badRequest().body(problemDetail);
    }

    /**
     * Handle unexpected errors (500 Internal Server Error).
     * This is a fallback for any unhandled exceptions.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGenericException(Exception ex) {
        ProblemDetail problemDetail = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        problemDetail.setTitle("Internal Server Error");
        problemDetail.setDetail("An unexpected error occurred");
        problemDetail.setType(URI.create("/problems/internal-error"));
        
        logger.error("Unexpected error", ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(problemDetail);
    }
}