package com.example.legacyshop.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.stereotype.Service;

import javax.sql.DataSource;
import java.sql.Connection;

/**
 * Service for health check operations.
 * 
 * Key patterns:
 * - Database connection validation
 * - Version information from build properties
 * - Simple health status determination
 */
@Service
public class HealthCheckService {

    private final DataSource dataSource;
    private final BuildProperties buildProperties;

    @Autowired(required = false)
    public HealthCheckService(DataSource dataSource, BuildProperties buildProperties) {
        this.dataSource = dataSource;
        this.buildProperties = buildProperties;
    }

    /**
     * Check if the database is connected.
     * @return "connected" if database is accessible, "disconnected" otherwise
     */
    public String checkDatabaseStatus() {
        try (Connection connection = dataSource.getConnection()) {
            // Simple validation query
            return connection.isValid(1) ? "connected" : "disconnected";
        } catch (Exception e) {
            return "disconnected";
        }
    }

    /**
     * Get application version from build properties.
     * @return version string or "unknown" if not available
     */
    public String getApplicationVersion() {
        if (buildProperties != null) {
            return buildProperties.getVersion();
        }
        // Fallback for development environment where build-info.properties may not exist
        return "0.0.1-SNAPSHOT";
    }

    /**
     * Determine overall health status.
     * @return "UP" if database is connected, "DOWN" otherwise
     */
    public String getHealthStatus() {
        String dbStatus = checkDatabaseStatus();
        return "connected".equals(dbStatus) ? "UP" : "DOWN";
    }
}
