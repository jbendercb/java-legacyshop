package com.example.legacyshop.service;

import com.example.legacyshop.dto.HealthResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for HealthCheckService.
 * 
 * Tests cover:
 * - Database connectivity check success
 * - Database connectivity check failure
 * - System status determination based on database status
 * - Timestamp and version inclusion
 */
@ExtendWith(MockitoExtension.class)
class HealthCheckServiceTest {

    @Mock
    private JdbcTemplate jdbcTemplate;

    @InjectMocks
    private HealthCheckService healthCheckService;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(healthCheckService, "applicationVersion", "0.0.1-SNAPSHOT");
    }

    @Test
    void checkHealth_WhenDatabaseIsConnected_ReturnsUpStatus() {
        // Given
        when(jdbcTemplate.queryForObject(eq("SELECT 1"), eq(Integer.class))).thenReturn(1);

        // When
        HealthResponse response = healthCheckService.checkHealth();

        // Then
        assertNotNull(response);
        assertEquals("UP", response.getStatus());
        assertEquals("connected", response.getDatabase());
        assertEquals("0.0.1-SNAPSHOT", response.getVersion());
        assertNotNull(response.getTimestamp());

        verify(jdbcTemplate).queryForObject(eq("SELECT 1"), eq(Integer.class));
    }

    @Test
    void checkHealth_WhenDatabaseIsDisconnected_ReturnsDownStatus() {
        // Given
        when(jdbcTemplate.queryForObject(eq("SELECT 1"), eq(Integer.class)))
            .thenThrow(new RuntimeException("Connection refused"));

        // When
        HealthResponse response = healthCheckService.checkHealth();

        // Then
        assertNotNull(response);
        assertEquals("DOWN", response.getStatus());
        assertEquals("disconnected", response.getDatabase());
        assertEquals("0.0.1-SNAPSHOT", response.getVersion());
        assertNotNull(response.getTimestamp());

        verify(jdbcTemplate).queryForObject(eq("SELECT 1"), eq(Integer.class));
    }

    @Test
    void checkHealth_TimestampIsInISO8601Format() {
        // Given
        when(jdbcTemplate.queryForObject(eq("SELECT 1"), eq(Integer.class))).thenReturn(1);

        // When
        HealthResponse response = healthCheckService.checkHealth();

        // Then
        assertNotNull(response.getTimestamp());
        // Verify ISO-8601 format (contains 'T' and 'Z')
        assertTrue(response.getTimestamp().contains("T"));
        assertTrue(response.getTimestamp().endsWith("Z"));
    }

    @Test
    void checkHealth_IncludesVersionFromProperties() {
        // Given
        when(jdbcTemplate.queryForObject(eq("SELECT 1"), eq(Integer.class))).thenReturn(1);

        // When
        HealthResponse response = healthCheckService.checkHealth();

        // Then
        assertEquals("0.0.1-SNAPSHOT", response.getVersion());
    }
}