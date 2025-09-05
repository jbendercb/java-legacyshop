package com.example.legacyshop.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.time.LocalDateTime;

/**
 * IdempotencyRecord entity for preventing duplicate operations.
 * 
 * Key patterns:
 * - Unique constraint on idempotency key
 * - TTL-style cleanup (could be enhanced with scheduled cleanup)
 * - Result caching for identical requests
 */
@Entity
@Table(name = "idempotency_records",
       uniqueConstraints = @UniqueConstraint(name = "uk_idempotency_key", columnNames = "idempotencyKey"))
public class IdempotencyRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "Idempotency key is required")
    @Size(max = 100, message = "Idempotency key must not exceed 100 characters")
    @Column(nullable = false, unique = true, length = 100)
    private String idempotencyKey;

    @NotBlank(message = "Operation type is required")
    @Size(max = 50, message = "Operation type must not exceed 50 characters")
    @Column(nullable = false, length = 50)
    private String operationType;

    @Column
    private Long resultEntityId;

    @Column(length = 1000)
    private String resultData;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    // Constructors
    public IdempotencyRecord() {}

    public IdempotencyRecord(String idempotencyKey, String operationType) {
        this.idempotencyKey = idempotencyKey;
        this.operationType = operationType;
    }

    // Business methods
    public boolean isExpired(int hoursToLive) {
        return createdAt.isBefore(LocalDateTime.now().minusHours(hoursToLive));
    }

    public void setResult(Long entityId, String resultData) {
        this.resultEntityId = entityId;
        this.resultData = resultData;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getIdempotencyKey() { return idempotencyKey; }
    public void setIdempotencyKey(String idempotencyKey) { this.idempotencyKey = idempotencyKey; }

    public String getOperationType() { return operationType; }
    public void setOperationType(String operationType) { this.operationType = operationType; }

    public Long getResultEntityId() { return resultEntityId; }
    public void setResultEntityId(Long resultEntityId) { this.resultEntityId = resultEntityId; }

    public String getResultData() { return resultData; }
    public void setResultData(String resultData) { this.resultData = resultData; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}