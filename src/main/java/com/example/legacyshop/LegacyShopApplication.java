package com.example.legacyshop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Main Spring Boot application class for LegacyShop.
 * 
 * This monolith demonstrates 10 common enterprise patterns:
 * 1. Product CRUD with validation and SKU uniqueness
 * 2. Order placement pipeline with atomic transactions
 * 3. Payment authorization with retry logic
 * 4. Order cancellation with compensating actions
 * 5. Scheduled inventory replenishment
 * 6. Loyalty points accrual system
 * 7. Config-driven promotions
 * 8. Paginated reporting with N+1 prevention
 * 9. Problem-Details JSON error handling
 * 10. Idempotency via headers
 */
@SpringBootApplication
@EnableRetry  // Enables @Retryable annotation for payment retry logic
@EnableScheduling  // Enables @Scheduled annotation for nightly replenishment
public class LegacyShopApplication {

    public static void main(String[] args) {
        SpringApplication.run(LegacyShopApplication.class, args);
    }
}