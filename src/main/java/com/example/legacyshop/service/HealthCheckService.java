package com.example.legacyshop.service;

import com.example.legacyshop.dto.HealthResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;

/**
 * Service for checking system health status.
 * 
 * Key patterns:
 * - Lightweight database connectivity check using JdbcTemplate
 * - Version info from application properties
 * - Graceful error handling for database failures
 * - ISO-8601 timestamp format
 */
@Service
public class HealthCheckService {

    private static final Logger log = LoggerFactory.getLogger(HealthCheckService.class);

    private final JdbcTemplate jdbcTemplate;
    
    @Value("${application.version:unknown}")
    private String applicationVersion;

    public HealthCheckService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    /**
     * Check system health and return comprehensive status.
     * 
     * @return HealthResponse with current system status
     */
    public HealthResponse checkHealth() {
        String timestamp = Instant.now().toString();
        String databaseStatus = checkDatabaseConnection();
        String systemStatus = "connected".equals(databaseStatus) ? "UP" : "DOWN";

        return new HealthResponse(
            systemStatus,
            timestamp,
            applicationVersion,
            databaseStatus
        );
    }

    /**
     * Check database connectivity using a lightweight query.
     * 
     * @return "connected" if database is accessible, error message otherwise
     */
    private String checkDatabaseConnection() {
        try {
            // Use lightweight query to check database connectivity
            jdbcTemplate.queryForObject("SELECT 1", Integer.class);
            return "connected";
        } catch (Exception e) {
            log.error("Database health check failed", e);
            return "disconnected";
        }
    }
}