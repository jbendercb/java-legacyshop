package com.example.legacyshop.controller;

import com.example.legacyshop.dto.HealthCheckResponse;
import com.example.legacyshop.service.HealthCheckService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * REST controller for health check endpoint.
 * 
 * Key patterns:
 * - No authentication required
 * - Returns appropriate HTTP status codes
 * - Simple JSON response with system health information
 */
@RestController
@RequestMapping("/api/health")
public class HealthCheckController {

    private final HealthCheckService healthCheckService;

    public HealthCheckController(HealthCheckService healthCheckService) {
        this.healthCheckService = healthCheckService;
    }

    /**
     * Health check endpoint.
     * GET /api/health
     * 
     * Returns:
     * - 200 OK when system is healthy (database connected)
     * - 503 Service Unavailable when database is disconnected
     */
    @GetMapping
    public ResponseEntity<HealthCheckResponse> healthCheck() {
        String status = healthCheckService.getHealthStatus();
        String version = healthCheckService.getApplicationVersion();
        String database = healthCheckService.checkDatabaseStatus();

        HealthCheckResponse response = HealthCheckResponse.create(status, version, database);

        // Return 503 if database is unavailable
        if ("DOWN".equals(status)) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
        }

        return ResponseEntity.ok(response);
    }
}
