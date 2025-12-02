package com.example.legacyshop.dto;

import java.time.Instant;

/**
 * Response DTO for health check endpoint.
 * 
 * Returns system health information including:
 * - System status (UP/DOWN)
 * - Current timestamp
 * - Application version
 * - Database connection status
 */
public class HealthResponse {

    private String status;
    private String timestamp;
    private String version;
    private String database;

    public HealthResponse() {
    }

    public HealthResponse(String status, String timestamp, String version, String database) {
        this.status = status;
        this.timestamp = timestamp;
        this.version = version;
        this.database = database;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getDatabase() {
        return database;
    }

    public void setDatabase(String database) {
        this.database = database;
    }
}