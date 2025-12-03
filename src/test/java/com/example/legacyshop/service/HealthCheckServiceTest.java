package com.example.legacyshop.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.info.BuildProperties;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.*;

/**
 * Unit tests for HealthCheckService.
 * 
 * Tests cover:
 * - Database connection validation
 * - Health status determination
 * - Version retrieval
 * - Error handling scenarios
 */
@ExtendWith(MockitoExtension.class)
class HealthCheckServiceTest {

    @Mock
    private DataSource dataSource;

    @Mock
    private BuildProperties buildProperties;

    @Mock
    private Connection connection;

    private HealthCheckService healthCheckService;

    @BeforeEach
    void setUp() {
        healthCheckService = new HealthCheckService(dataSource, buildProperties);
    }

    @Test
    void checkDatabaseStatus_WhenConnected_ReturnsConnected() throws SQLException {
        // Given
        when(dataSource.getConnection()).thenReturn(connection);
        when(connection.isValid(1)).thenReturn(true);

        // When
        String status = healthCheckService.checkDatabaseStatus();

        // Then
        assertEquals("connected", status);
        verify(dataSource).getConnection();
        verify(connection).isValid(1);
        verify(connection).close();
    }

    @Test
    void checkDatabaseStatus_WhenConnectionInvalid_ReturnsDisconnected() throws SQLException {
        // Given
        when(dataSource.getConnection()).thenReturn(connection);
        when(connection.isValid(1)).thenReturn(false);

        // When
        String status = healthCheckService.checkDatabaseStatus();

        // Then
        assertEquals("disconnected", status);
        verify(dataSource).getConnection();
        verify(connection).isValid(1);
    }

    @Test
    void checkDatabaseStatus_WhenExceptionThrown_ReturnsDisconnected() throws SQLException {
        // Given
        when(dataSource.getConnection()).thenThrow(new SQLException("Connection failed"));

        // When
        String status = healthCheckService.checkDatabaseStatus();

        // Then
        assertEquals("disconnected", status);
        verify(dataSource).getConnection();
    }

    @Test
    void getApplicationVersion_WhenBuildPropertiesAvailable_ReturnsVersion() {
        // Given
        when(buildProperties.getVersion()).thenReturn("1.0.0");

        // When
        String version = healthCheckService.getApplicationVersion();

        // Then
        assertEquals("1.0.0", version);
        verify(buildProperties).getVersion();
    }

    @Test
    void getApplicationVersion_WhenBuildPropertiesNull_ReturnsDefault() {
        // Given
        HealthCheckService serviceWithNullBuildProps = new HealthCheckService(dataSource, null);

        // When
        String version = serviceWithNullBuildProps.getApplicationVersion();

        // Then
        assertEquals("0.0.1-SNAPSHOT", version);
    }

    @Test
    void getHealthStatus_WhenDatabaseConnected_ReturnsUP() throws SQLException {
        // Given
        when(dataSource.getConnection()).thenReturn(connection);
        when(connection.isValid(anyInt())).thenReturn(true);

        // When
        String status = healthCheckService.getHealthStatus();

        // Then
        assertEquals("UP", status);
    }

    @Test
    void getHealthStatus_WhenDatabaseDisconnected_ReturnsDOWN() throws SQLException {
        // Given
        when(dataSource.getConnection()).thenThrow(new SQLException("Connection failed"));

        // When
        String status = healthCheckService.getHealthStatus();

        // Then
        assertEquals("DOWN", status);
    }
}
