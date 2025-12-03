package com.example.legacyshop.controller;

import com.example.legacyshop.dto.HealthCheckResponse;
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
 * - Healthy system response (200 OK)
 * - Unhealthy system response (503 Service Unavailable)
 * - Response body validation
 */
@ExtendWith(MockitoExtension.class)
class HealthCheckControllerTest {

    @Mock
    private HealthCheckService healthCheckService;

    @InjectMocks
    private HealthCheckController healthCheckController;

    @Test
    void healthCheck_WhenSystemHealthy_Returns200OK() {
        // Given
        when(healthCheckService.getHealthStatus()).thenReturn("UP");
        when(healthCheckService.getApplicationVersion()).thenReturn("1.0.0");
        when(healthCheckService.checkDatabaseStatus()).thenReturn("connected");

        // When
        ResponseEntity<HealthCheckResponse> response = healthCheckController.healthCheck();

        // Then
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("UP", response.getBody().getStatus());
        assertEquals("1.0.0", response.getBody().getVersion());
        assertEquals("connected", response.getBody().getDatabase());
        assertNotNull(response.getBody().getTimestamp());

        verify(healthCheckService).getHealthStatus();
        verify(healthCheckService).getApplicationVersion();
        verify(healthCheckService).checkDatabaseStatus();
    }

    @Test
    void healthCheck_WhenDatabaseUnavailable_Returns503() {
        // Given
        when(healthCheckService.getHealthStatus()).thenReturn("DOWN");
        when(healthCheckService.getApplicationVersion()).thenReturn("1.0.0");
        when(healthCheckService.checkDatabaseStatus()).thenReturn("disconnected");

        // When
        ResponseEntity<HealthCheckResponse> response = healthCheckController.healthCheck();

        // Then
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("DOWN", response.getBody().getStatus());
        assertEquals("1.0.0", response.getBody().getVersion());
        assertEquals("disconnected", response.getBody().getDatabase());
        assertNotNull(response.getBody().getTimestamp());

        verify(healthCheckService).getHealthStatus();
        verify(healthCheckService).getApplicationVersion();
        verify(healthCheckService).checkDatabaseStatus();
    }

    @Test
    void healthCheck_ResponseContainsTimestamp() {
        // Given
        when(healthCheckService.getHealthStatus()).thenReturn("UP");
        when(healthCheckService.getApplicationVersion()).thenReturn("1.0.0");
        when(healthCheckService.checkDatabaseStatus()).thenReturn("connected");

        // When
        ResponseEntity<HealthCheckResponse> response = healthCheckController.healthCheck();

        // Then
        assertNotNull(response.getBody());
        assertNotNull(response.getBody().getTimestamp());
        // Verify timestamp format (ISO-8601)
        assertTrue(response.getBody().getTimestamp().matches("\\d{4}-\\d{2}-\\d{2}T.*"));
    }
}
