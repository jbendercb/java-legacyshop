package com.example.legacyshop.repository;

import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.entity.OrderEntity.OrderStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.Optional;

/**
 * Repository for Order entity operations.
 * 
 * Key patterns:
 * - Idempotency key lookup
 * - Status-based queries
 * - Join fetch to prevent N+1 queries in reports
 * - Date range queries for reporting
 */
@Repository
public interface OrderRepository extends JpaRepository<OrderEntity, Long> {

    /**
     * Find order by idempotency key (for duplicate prevention).
     */
    Optional<OrderEntity> findByIdempotencyKey(String idempotencyKey);

    /**
     * Find orders by customer with pagination.
     */
    @Query("SELECT o FROM OrderEntity o JOIN FETCH o.customer WHERE o.customer.id = :customerId")
    Page<OrderEntity> findByCustomerId(Long customerId, Pageable pageable);

    /**
     * Find orders by status with pagination.
     */
    Page<OrderEntity> findByStatus(OrderStatus status, Pageable pageable);

    /**
     * Find orders within date range for reporting (with join fetch to prevent N+1).
     */
    @Query("SELECT o FROM OrderEntity o " +
           "JOIN FETCH o.customer " +
           "LEFT JOIN FETCH o.items " +
           "WHERE o.createdAt BETWEEN :startDate AND :endDate")
    Page<OrderEntity> findOrdersForReport(LocalDateTime startDate, LocalDateTime endDate, Pageable pageable);

    /**
     * Find PAID orders for loyalty points processing.
     */
    @Query("SELECT o FROM OrderEntity o WHERE o.status = 'PAID' AND o.updatedAt >= :since")
    Page<OrderEntity> findPaidOrdersSince(LocalDateTime since, Pageable pageable);
}