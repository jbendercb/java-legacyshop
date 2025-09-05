package com.example.legacyshop.repository;

import com.example.legacyshop.entity.IdempotencyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.Optional;

/**
 * Repository for IdempotencyRecord entity operations.
 * 
 * Key patterns:
 * - Idempotency key lookup
 * - Cleanup of expired records
 * - Operation type filtering
 */
@Repository
public interface IdempotencyRecordRepository extends JpaRepository<IdempotencyRecord, Long> {

    /**
     * Find existing idempotency record by key.
     */
    Optional<IdempotencyRecord> findByIdempotencyKey(String idempotencyKey);

    /**
     * Check if idempotency key exists.
     */
    boolean existsByIdempotencyKey(String idempotencyKey);

    /**
     * Delete expired idempotency records (cleanup job).
     */
    @Modifying
    @Query("DELETE FROM IdempotencyRecord i WHERE i.createdAt < :cutoffDate")
    int deleteExpiredRecords(LocalDateTime cutoffDate);

    /**
     * Find records by operation type (for monitoring).
     */
    @Query("SELECT i FROM IdempotencyRecord i WHERE i.operationType = :operationType ORDER BY i.createdAt DESC")
    java.util.List<IdempotencyRecord> findByOperationType(String operationType);
}