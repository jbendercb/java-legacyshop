package com.example.legacyshop.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.time.LocalDateTime;

/**
 * AuditLog entity for tracking business operations.
 * 
 * Key patterns:
 * - Immutable audit records (no updates after creation)
 * - Generic event tracking with operation type and entity details
 * - Used for scheduled replenishment tracking
 */
@Entity
@Table(name = "audit_logs")
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OperationType operation;

    @NotBlank(message = "Entity type is required")
    @Size(max = 50, message = "Entity type must not exceed 50 characters")
    @Column(nullable = false, length = 50)
    private String entityType;

    @Column
    private Long entityId;

    @Size(max = 1000, message = "Details must not exceed 1000 characters")
    @Column(length = 1000)
    private String details;

    @Column(nullable = false, updatable = false)
    private LocalDateTime timestamp;

    @PrePersist
    protected void onCreate() {
        timestamp = LocalDateTime.now();
    }

    // Constructors
    public AuditLog() {}

    public AuditLog(OperationType operation, String entityType, Long entityId, String details) {
        this.operation = operation;
        this.entityType = entityType;
        this.entityId = entityId;
        this.details = details;
    }

    // Static factory methods for common audit events
    public static AuditLog replenishmentLog(Long productId, String productSku, int quantity) {
        String details = String.format("Replenished %d units of product %s", quantity, productSku);
        return new AuditLog(OperationType.INVENTORY_REPLENISHMENT, "Product", productId, details);
    }

    public static AuditLog orderCreatedLog(Long orderId, String customerEmail) {
        String details = String.format("Order created for customer %s", customerEmail);
        return new AuditLog(OperationType.ORDER_CREATED, "Order", orderId, details);
    }

    public static AuditLog orderCancelledLog(Long orderId, String reason) {
        String details = String.format("Order cancelled: %s", reason);
        return new AuditLog(OperationType.ORDER_CANCELLED, "Order", orderId, details);
    }

    public static AuditLog loyaltyPointsLog(Long customerId, int pointsAdded) {
        String details = String.format("Added %d loyalty points", pointsAdded);
        return new AuditLog(OperationType.LOYALTY_POINTS_ADDED, "Customer", customerId, details);
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public OperationType getOperation() { return operation; }
    public void setOperation(OperationType operation) { this.operation = operation; }

    public String getEntityType() { return entityType; }
    public void setEntityType(String entityType) { this.entityType = entityType; }

    public Long getEntityId() { return entityId; }
    public void setEntityId(Long entityId) { this.entityId = entityId; }

    public String getDetails() { return details; }
    public void setDetails(String details) { this.details = details; }

    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }

    // Enums
    public enum OperationType {
        ORDER_CREATED,
        ORDER_CANCELLED,
        PAYMENT_AUTHORIZED,
        PAYMENT_VOIDED,
        INVENTORY_REPLENISHMENT,
        LOYALTY_POINTS_ADDED,
        PRODUCT_CREATED,
        PRODUCT_UPDATED
    }
}