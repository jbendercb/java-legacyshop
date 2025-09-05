package com.example.legacyshop.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Payment entity for tracking payment authorization and status.
 * 
 * Key patterns:
 * - One-to-one relationship with Order
 * - Payment status workflow
 * - External authorization ID tracking
 * - Retry attempt tracking
 */
@Entity
@Table(name = "payments")
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id", nullable = false)
    private OrderEntity order;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private PaymentStatus status = PaymentStatus.PENDING;

    @NotNull(message = "Amount is required")
    @DecimalMin(value = "0.01", message = "Amount must be at least 0.01")
    @Digits(integer = 10, fraction = 2)
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal amount;

    @Size(max = 100, message = "External authorization ID must not exceed 100 characters")
    @Column(length = 100)
    private String externalAuthorizationId;

    @Column(nullable = false)
    private Integer retryAttempts = 0;

    @Column(length = 500)
    private String errorMessage;

    // Audit fields
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Version
    private Long version;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    // Constructors
    public Payment() {}

    public Payment(OrderEntity order, BigDecimal amount) {
        this.order = order;
        this.amount = amount;
    }

    // Business methods
    public void authorize(String externalAuthorizationId) {
        this.externalAuthorizationId = externalAuthorizationId;
        this.status = PaymentStatus.AUTHORIZED;
        this.errorMessage = null;
    }

    public void fail(String errorMessage) {
        this.status = PaymentStatus.FAILED;
        this.errorMessage = errorMessage;
    }

    public void voidPayment() {
        if (status != PaymentStatus.AUTHORIZED) {
            throw new IllegalStateException("Can only void authorized payments");
        }
        this.status = PaymentStatus.VOIDED;
    }

    public void incrementRetryAttempts() {
        this.retryAttempts++;
    }

    public boolean canRetry() {
        return retryAttempts < 2 && status == PaymentStatus.FAILED;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public OrderEntity getOrder() { return order; }
    public void setOrder(OrderEntity order) { this.order = order; }

    public PaymentStatus getStatus() { return status; }
    public void setStatus(PaymentStatus status) { this.status = status; }

    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }

    public String getExternalAuthorizationId() { return externalAuthorizationId; }
    public void setExternalAuthorizationId(String externalAuthorizationId) { 
        this.externalAuthorizationId = externalAuthorizationId; 
    }

    public Integer getRetryAttempts() { return retryAttempts; }
    public void setRetryAttempts(Integer retryAttempts) { this.retryAttempts = retryAttempts; }

    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }

    // Enums
    public enum PaymentStatus {
        PENDING,        // Payment created, awaiting authorization
        AUTHORIZED,     // Payment authorized by external service
        FAILED,         // Payment authorization failed
        VOIDED          // Payment voided (compensation for order cancellation)
    }
}