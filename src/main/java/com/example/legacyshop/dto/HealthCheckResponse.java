package com.example.legacyshop.dto;

import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

/**
 * DTO for health check responses.
 * 
 * Key patterns:
 * - Immutable response object
 * - ISO-8601 formatted timestamp
 * - Simple status indicators
 */
public class HealthCheckResponse {

    private final String status;
    private final String timestamp;
    private final String version;
    private final String database;

    public HealthCheckResponse(String status, String timestamp, String version, String database) {
        this.status = status;
        this.timestamp = timestamp;
        this.version = version;
        this.database = database;
    }

    /**
     * Create a health check response with current timestamp.
     */
    public static HealthCheckResponse create(String status, String version, String database) {
        String timestamp = LocalDateTime.now(ZoneOffset.UTC)
            .format(DateTimeFormatter.ISO_DATE_TIME);
        return new HealthCheckResponse(status, timestamp, version, database);
    }

    // Getters
    public String getStatus() { return status; }
    public String getTimestamp() { return timestamp; }
    public String getVersion() { return version; }
    public String getDatabase() { return database; }
}
