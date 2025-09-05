package com.example.legacyshop.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Mock external payment service controller for testing.
 * 
 * This simulates an external payment gateway that:
 * - Returns 200 with authorizationId for most requests
 * - Returns 400 for invalid amounts (< 0.01)
 * - Returns 500 randomly to test retry logic
 * - Returns 402 for amounts > 1000 (insufficient funds simulation)
 */
@RestController
@RequestMapping("/mock/payment")
public class MockPaymentController {

    /**
     * Mock payment authorization endpoint.
     * Demonstrates various response scenarios for testing.
     */
    @PostMapping("/authorize")
    public ResponseEntity<?> authorize(@RequestBody Map<String, Object> request) {
        try {
            String amountStr = (String) request.get("amount");
            BigDecimal amount = new BigDecimal(amountStr);

            // Simulate validation error (4xx - not retryable)
            if (amount.compareTo(new BigDecimal("0.01")) < 0) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "Amount must be at least 0.01"));
            }

            // Simulate insufficient funds (4xx - not retryable)
            if (amount.compareTo(new BigDecimal("1000.00")) > 0) {
                return ResponseEntity.status(HttpStatus.PAYMENT_REQUIRED)
                    .body(Map.of("error", "Insufficient funds"));
            }

            // Randomly simulate server error (5xx - retryable)
            if (ThreadLocalRandom.current().nextDouble() < 0.1) { // 10% chance
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Payment service temporarily unavailable"));
            }

            // Success case
            String authorizationId = "AUTH_" + UUID.randomUUID().toString();
            return ResponseEntity.ok(Map.of(
                "authorizationId", authorizationId,
                "status", "AUTHORIZED",
                "amount", amount.toString()
            ));

        } catch (Exception e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid request: " + e.getMessage()));
        }
    }

    /**
     * Mock payment void endpoint.
     */
    @PostMapping("/void")
    public ResponseEntity<?> voidPayment(@RequestBody Map<String, Object> request) {
        String authorizationId = (String) request.get("authorizationId");

        if (authorizationId == null || authorizationId.isEmpty()) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Authorization ID is required"));
        }

        // Randomly simulate server error
        if (ThreadLocalRandom.current().nextDouble() < 0.05) { // 5% chance
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Void service temporarily unavailable"));
        }

        return ResponseEntity.ok(Map.of(
            "authorizationId", authorizationId,
            "status", "VOIDED"
        ));
    }
}