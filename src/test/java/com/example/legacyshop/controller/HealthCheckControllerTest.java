package com.example.legacyshop.controller;

import com.example.legacyshop.dto.HealthResponse;
import com.example.legacyshop.service.HealthCheckService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for HealthCheckController.
 * 
 * Tests cover:
 * - Healthy system returns 200 OK
 * - Unhealthy system returns 503 Service Unavailable
 * - Response contains all required fields
 */
@ExtendWith(MockitoExtension.class)
class HealthCheckControllerTest {

    @Mock
    private HealthCheckService healthCheckService;

    @InjectMocks
    private HealthCheckController healthCheckController;

    @Test
    void health_WhenSystemIsHealthy_Returns200() {
        // Given
        HealthResponse healthyResponse = new HealthResponse(
            "UP",
            "2025-12-02T10:30:00Z",
            "0.0.1-SNAPSHOT",
            "connected"
        );
        when(healthCheckService.checkHealth()).thenReturn(healthyResponse);

        // When
        ResponseEntity<HealthResponse> response = healthCheckController.health();

        // Then
        assertNotNull(response);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("UP", response.getBody().getStatus());
        assertEquals("0.0.1-SNAPSHOT", response.getBody().getVersion());
        assertEquals("connected", response.getBody().getDatabase());
        assertNotNull(response.getBody().getTimestamp());

        verify(healthCheckService).checkHealth();
    }

    @Test
    void health_WhenDatabaseIsDown_Returns503() {
        // Given
        HealthResponse unhealthyResponse = new HealthResponse(
            "DOWN",
            "2025-12-02T10:30:00Z",
            "0.0.1-SNAPSHOT",
            "disconnected"
        );
        when(healthCheckService.checkHealth()).thenReturn(unhealthyResponse);

        // When
        ResponseEntity<HealthResponse> response = healthCheckController.health();

        // Then
        assertNotNull(response);
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("DOWN", response.getBody().getStatus());
        assertEquals("disconnected", response.getBody().getDatabase());

        verify(healthCheckService).checkHealth();
    }

    @Test
    void health_ResponseContainsAllRequiredFields() {
        // Given
        HealthResponse healthResponse = new HealthResponse(
            "UP",
            "2025-12-02T10:30:00Z",
            "0.0.1-SNAPSHOT",
            "connected"
        );
        when(healthCheckService.checkHealth()).thenReturn(healthResponse);

        // When
        ResponseEntity<HealthResponse> response = healthCheckController.health();

        // Then
        assertNotNull(response.getBody());
        assertNotNull(response.getBody().getStatus());
        assertNotNull(response.getBody().getTimestamp());
        assertNotNull(response.getBody().getVersion());
        assertNotNull(response.getBody().getDatabase());
    }
}