package com.example.legacyshop.repository;

import com.example.legacyshop.entity.Payment;
import com.example.legacyshop.entity.Payment.PaymentStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository for Payment entity operations.
 * 
 * Key patterns:
 * - Status-based queries
 * - External authorization ID lookup
 * - Failed payment retry identification
 */
@Repository
public interface PaymentRepository extends JpaRepository<Payment, Long> {

    /**
     * Find payment by order ID.
     */
    Optional<Payment> findByOrderId(Long orderId);

    /**
     * Find payment by external authorization ID (for webhook processing).
     */
    Optional<Payment> findByExternalAuthorizationId(String externalAuthorizationId);

    /**
     * Find payments by status.
     */
    List<Payment> findByStatus(PaymentStatus status);

    /**
     * Find failed payments that can be retried.
     */
    @Query("SELECT p FROM Payment p WHERE p.status = 'FAILED' AND p.retryAttempts < 2")
    List<Payment> findFailedPaymentsEligibleForRetry();
}