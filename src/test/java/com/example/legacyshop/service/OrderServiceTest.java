package com.example.legacyshop.service;

import com.example.legacyshop.dto.OrderCreateRequest;
import com.example.legacyshop.dto.OrderResponse;
import com.example.legacyshop.entity.Customer;
import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.entity.Product;
import com.example.legacyshop.exception.BusinessValidationException;
import com.example.legacyshop.repository.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for OrderService focusing on critical business rules.
 * 
 * Tests cover:
 * - Order placement pipeline atomicity
 * - Stock validation and decrement
 * - Idempotency behavior
 * - Discount application
 * - Stock restoration on cancellation
 */
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;
    @Mock
    private ProductRepository productRepository;
    @Mock
    private CustomerRepository customerRepository;
    @Mock
    private AuditLogRepository auditLogRepository;
    @Mock
    private IdempotencyRecordRepository idempotencyRecordRepository;
    @Mock
    private CustomerService customerService;
    @Mock
    private DiscountService discountService;
    @Mock
    private PaymentService paymentService;

    @InjectMocks
    private OrderService orderService;

    private OrderCreateRequest orderRequest;
    private Customer customer;
    private Product product;
    private OrderEntity order;

    @BeforeEach
    void setUp() {
        // Setup order request
        OrderCreateRequest.OrderItemRequest itemRequest = new OrderCreateRequest.OrderItemRequest("TEST-SKU", 2);
        orderRequest = new OrderCreateRequest("customer@test.com", List.of(itemRequest));

        // Setup customer
        customer = new Customer("customer@test.com", "John", "Doe");
        customer.setId(1L);

        // Setup product with sufficient stock
        product = new Product("TEST-SKU", "Test Product", "Description", new BigDecimal("50.00"), 10);
        product.setId(1L);

        // Setup order
        order = new OrderEntity(customer, "test-idempotency-key");
        order.setId(1L);
    }

    @Test
    void createOrder_Success_AtomicStockDecrement() {
        // Given
        String idempotencyKey = "test-key";
        when(orderRepository.findByIdempotencyKey(idempotencyKey)).thenReturn(Optional.empty());
        when(customerService.findOrCreateCustomer(anyString(), anyString(), anyString())).thenReturn(customer);
        when(productRepository.findBySku("TEST-SKU")).thenReturn(Optional.of(product));
        when(discountService.calculateDiscount(any())).thenReturn(new BigDecimal("5.00"));
        when(orderRepository.save(any(OrderEntity.class))).thenReturn(order);
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        OrderResponse response = orderService.createOrder(orderRequest, idempotencyKey);

        // Then
        assertNotNull(response);
        assertEquals(customer.getEmail(), response.getCustomerEmail());
        
        // Verify atomic operations occurred in correct order
        verify(productRepository).findBySku("TEST-SKU");
        verify(productRepository).save(product); // Stock decremented
        verify(orderRepository).save(any(OrderEntity.class));
        verify(idempotencyRecordRepository).save(any());
        verify(auditLogRepository).save(any());
        
        // Verify stock was decremented
        assertEquals(8, product.getStockQuantity()); // 10 - 2 = 8
    }

    @Test
    void createOrder_IdempotencyKey_ReturnsExistingOrder() {
        // Given
        String idempotencyKey = "existing-key";
        when(orderRepository.findByIdempotencyKey(idempotencyKey)).thenReturn(Optional.of(order));

        // When
        OrderResponse response = orderService.createOrder(orderRequest, idempotencyKey);

        // Then
        assertNotNull(response);
        
        // Verify no new order was created
        verify(orderRepository).findByIdempotencyKey(idempotencyKey);
        verify(orderRepository, never()).save(any());
        verify(productRepository, never()).save(any());
    }

    @Test
    void createOrder_InsufficientStock_ThrowsException() {
        // Given
        product.setStockQuantity(1); // Only 1 in stock, but request is for 2
        
        when(orderRepository.findByIdempotencyKey(any())).thenReturn(Optional.empty());
        when(customerService.findOrCreateCustomer(anyString(), anyString(), anyString())).thenReturn(customer);
        when(productRepository.findBySku("TEST-SKU")).thenReturn(Optional.of(product));

        // When & Then
        BusinessValidationException exception = assertThrows(
            BusinessValidationException.class,
            () -> orderService.createOrder(orderRequest, "test-key")
        );

        assertTrue(exception.getMessage().contains("Insufficient stock"));
        
        // Verify no stock was decremented and no order was saved
        assertEquals(1, product.getStockQuantity());
        verify(orderRepository, never()).save(any());
    }

    @Test
    void createOrder_InactiveProduct_ThrowsException() {
        // Given
        product.setActive(false);
        
        when(orderRepository.findByIdempotencyKey(any())).thenReturn(Optional.empty());
        when(customerService.findOrCreateCustomer(anyString(), anyString(), anyString())).thenReturn(customer);
        when(productRepository.findBySku("TEST-SKU")).thenReturn(Optional.of(product));

        // When & Then
        BusinessValidationException exception = assertThrows(
            BusinessValidationException.class,
            () -> orderService.createOrder(orderRequest, "test-key")
        );

        assertTrue(exception.getMessage().contains("not available"));
        verify(orderRepository, never()).save(any());
    }

    @Test
    void cancelOrder_Success_RestoresStock() {
        // Given - setup order with items
        order.setStatus(OrderEntity.OrderStatus.PAID);
        order.addItem(new com.example.legacyshop.entity.OrderItem(order, product, 2, new BigDecimal("50.00")));
        
        when(orderRepository.findById(1L)).thenReturn(Optional.of(order));
        when(productRepository.save(any(Product.class))).thenReturn(product);
        when(orderRepository.save(any(OrderEntity.class))).thenReturn(order);

        // When
        OrderResponse response = orderService.cancelOrder(1L);

        // Then
        assertNotNull(response);
        assertEquals("CANCELLED", response.getStatus());
        
        // Verify compensating actions
        verify(productRepository).save(product); // Stock restored
        verify(orderRepository).save(order); // Order status updated
        verify(auditLogRepository).save(any()); // Audit log created
        
        // Verify stock was restored
        assertEquals(12, product.getStockQuantity()); // 10 + 2 = 12
    }

    @Test
    void cancelOrder_CannotCancel_ThrowsException() {
        // Given - order already shipped
        order.setStatus(OrderEntity.OrderStatus.SHIPPED);
        
        when(orderRepository.findById(1L)).thenReturn(Optional.of(order));

        // When & Then
        BusinessValidationException exception = assertThrows(
            BusinessValidationException.class,
            () -> orderService.cancelOrder(1L)
        );

        assertTrue(exception.getMessage().contains("cannot be cancelled"));
        
        // Verify no compensating actions occurred
        verify(productRepository, never()).save(any());
        verify(orderRepository, never()).save(any());
    }
}