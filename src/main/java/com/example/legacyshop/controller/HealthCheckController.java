package com.example.legacyshop.controller;

import com.example.legacyshop.dto.HealthResponse;
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
 * - Public endpoint (no authentication required)
 * - Returns 200 OK when healthy
 * - Returns 503 Service Unavailable when database is down
 * - Provides system status, timestamp, version, and database status
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
     * - 200 OK with health info when system is healthy
     * - 503 Service Unavailable when database is down
     */
    @GetMapping
    public ResponseEntity<HealthResponse> health() {
        HealthResponse health = healthCheckService.checkHealth();
        
        // Return 503 if system is down
        if ("DOWN".equals(health.getStatus())) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(health);
        }
        
        return ResponseEntity.ok(health);
    }
}