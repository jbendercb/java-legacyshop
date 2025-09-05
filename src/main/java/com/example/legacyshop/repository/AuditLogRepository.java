package com.example.legacyshop.repository;

import com.example.legacyshop.entity.AuditLog;
import com.example.legacyshop.entity.AuditLog.OperationType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;

/**
 * Repository for AuditLog entity operations.
 * 
 * Key patterns:
 * - Operation type filtering
 * - Date range queries for audit trail
 * - Entity-specific audit log retrieval
 */
@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {

    /**
     * Find audit logs by operation type.
     */
    Page<AuditLog> findByOperation(OperationType operation, Pageable pageable);

    /**
     * Find audit logs for specific entity.
     */
    Page<AuditLog> findByEntityTypeAndEntityId(String entityType, Long entityId, Pageable pageable);

    /**
     * Find audit logs within date range.
     */
    Page<AuditLog> findByTimestampBetween(LocalDateTime startDate, LocalDateTime endDate, Pageable pageable);

    /**
     * Find recent audit logs (for monitoring/alerting).
     */
    Page<AuditLog> findByTimestampAfter(LocalDateTime since, Pageable pageable);
}