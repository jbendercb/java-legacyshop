package com.example.legacyshop.service;

import com.example.legacyshop.config.BusinessConfig;
import com.example.legacyshop.entity.Customer;
import com.example.legacyshop.entity.IdempotencyRecord;
import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.repository.AuditLogRepository;
import com.example.legacyshop.repository.CustomerRepository;
import com.example.legacyshop.repository.IdempotencyRecordRepository;
import com.example.legacyshop.repository.OrderRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for LoyaltyService focusing on business rules.
 * 
 * Tests cover:
 * - Idempotent points accrual (no double processing)
 * - Loyalty points cap enforcement (max 500 points)
 * - Correct points calculation from order total
 * - Only PAID orders processed
 */
@ExtendWith(MockitoExtension.class)
class LoyaltyServiceTest {

    @Mock
    private OrderRepository orderRepository;
    @Mock
    private CustomerRepository customerRepository;
    @Mock
    private AuditLogRepository auditLogRepository;
    @Mock
    private IdempotencyRecordRepository idempotencyRecordRepository;
    @Mock
    private BusinessConfig businessConfig;
    @Mock
    private BusinessConfig.Loyalty loyaltyConfig;

    @InjectMocks
    private LoyaltyService loyaltyService;

    private OrderEntity order;
    private Customer customer;

    @BeforeEach
    void setUp() {
        // Setup business config (using lenient for unused stubs)
        lenient().when(businessConfig.getLoyalty()).thenReturn(loyaltyConfig);
        lenient().when(loyaltyConfig.getPointsPerDollar()).thenReturn(1.0); // 1 point per dollar
        lenient().when(loyaltyConfig.getMaxPoints()).thenReturn(500); // Cap at 500 points

        // Setup customer
        customer = new Customer("customer@test.com", "John", "Doe");
        customer.setId(1L);
        customer.setLoyaltyPoints(450); // Near the cap

        // Setup PAID order
        order = new OrderEntity(customer, null);
        order.setId(1L);
        order.setStatus(OrderEntity.OrderStatus.PAID);
        order.setTotal(new BigDecimal("75.50")); // Should give 75 points
    }

    @Test
    void processOrderForLoyaltyPoints_Success_AddsCorrectPoints() {
        // Given - order not yet processed
        when(idempotencyRecordRepository.existsByIdempotencyKey("LOYALTY_1")).thenReturn(false);
        when(customerRepository.save(any(Customer.class))).thenReturn(customer);

        // When
        boolean processed = loyaltyService.processOrderForLoyaltyPoints(order);

        // Then
        assertTrue(processed);
        assertEquals(500, customer.getLoyaltyPoints()); // 450 + 50 (capped at 500, not 450 + 75)
        
        verify(idempotencyRecordRepository).existsByIdempotencyKey("LOYALTY_1");
        verify(customerRepository).save(customer);
        verify(idempotencyRecordRepository).save(any(IdempotencyRecord.class));
        verify(auditLogRepository).save(any());
    }

    @Test
    void processOrderForLoyaltyPoints_AlreadyProcessed_Idempotent() {
        // Given - order already processed
        when(idempotencyRecordRepository.existsByIdempotencyKey("LOYALTY_1")).thenReturn(true);

        // When
        boolean processed = loyaltyService.processOrderForLoyaltyPoints(order);

        // Then
        assertFalse(processed);
        
        verify(idempotencyRecordRepository).existsByIdempotencyKey("LOYALTY_1");
        verify(customerRepository, never()).save(any());
        verify(auditLogRepository, never()).save(any());
    }

    @Test
    void processOrderForLoyaltyPoints_NotPaidOrder_NotProcessed() {
        // Given - order not in PAID status
        order.setStatus(OrderEntity.OrderStatus.PENDING);
        when(idempotencyRecordRepository.existsByIdempotencyKey("LOYALTY_1")).thenReturn(false);

        // When
        boolean processed = loyaltyService.processOrderForLoyaltyPoints(order);

        // Then
        assertFalse(processed);
        
        verify(customerRepository, never()).save(any());
        verify(auditLogRepository, never()).save(any());
    }

    @Test
    void processOrderForLoyaltyPoints_EnforcesPointsCap() {
        // Given - customer already at max points
        customer.setLoyaltyPoints(500);
        when(idempotencyRecordRepository.existsByIdempotencyKey("LOYALTY_1")).thenReturn(false);
        when(customerRepository.save(any(Customer.class))).thenReturn(customer);

        // When
        boolean processed = loyaltyService.processOrderForLoyaltyPoints(order);

        // Then
        assertTrue(processed);
        assertEquals(500, customer.getLoyaltyPoints()); // Still capped at 500
        
        verify(customerRepository).save(customer);
    }

    @Test
    void processOrderForLoyaltyPoints_LowValueOrder_AddsCorrectPoints() {
        // Given - low value order that should give fewer points
        order.setTotal(new BigDecimal("5.25")); // Should give 5 points (floor of 5.25)
        customer.setLoyaltyPoints(100); // Well below cap
        
        when(idempotencyRecordRepository.existsByIdempotencyKey("LOYALTY_1")).thenReturn(false);
        when(customerRepository.save(any(Customer.class))).thenReturn(customer);

        // When
        boolean processed = loyaltyService.processOrderForLoyaltyPoints(order);

        // Then
        assertTrue(processed);
        assertEquals(105, customer.getLoyaltyPoints()); // 100 + 5
        
        verify(customerRepository).save(customer);
    }

    @Test
    void processOrderForLoyaltyPoints_ZeroValueOrder_NoPointsAdded() {
        // Given - zero value order
        order.setTotal(BigDecimal.ZERO);
        customer.setLoyaltyPoints(100);
        
        when(idempotencyRecordRepository.existsByIdempotencyKey("LOYALTY_1")).thenReturn(false);

        // When
        boolean processed = loyaltyService.processOrderForLoyaltyPoints(order);

        // Then
        assertFalse(processed); // No points to add, so not processed
        assertEquals(100, customer.getLoyaltyPoints()); // Unchanged
        
        verify(customerRepository, never()).save(any());
    }
}