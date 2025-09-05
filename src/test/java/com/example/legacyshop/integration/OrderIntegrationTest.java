package com.example.legacyshop.integration;

import com.example.legacyshop.dto.OrderCreateRequest;
import com.example.legacyshop.dto.OrderResponse;
import com.example.legacyshop.dto.ProductCreateRequest;
import com.example.legacyshop.entity.Customer;
import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.entity.Product;
import com.example.legacyshop.repository.CustomerRepository;
import com.example.legacyshop.repository.OrderRepository;
import com.example.legacyshop.repository.ProductRepository;
import com.example.legacyshop.service.OrderService;
import com.example.legacyshop.service.ProductService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for the complete order placement pipeline.
 * 
 * Tests the full flow:
 * 1. Customer creation
 * 2. Product stock validation
 * 3. Order creation with atomic stock decrement
 * 4. Discount application
 * 5. Database persistence
 * 6. Order cancellation with stock restoration
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class OrderIntegrationTest {

    @Autowired
    private OrderService orderService;

    @Autowired
    private ProductService productService;

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private CustomerRepository customerRepository;

    private Long productId;

    @BeforeEach
    void setUp() {
        // Clean up any existing test products first
        productRepository.findBySku("INTEGRATION-SKU").ifPresent(productRepository::delete);
        
        // Create test product with known stock
        ProductCreateRequest productRequest = new ProductCreateRequest(
            "INTEGRATION-SKU",
            "Integration Test Product",
            "Test Description",
            new BigDecimal("100.00"), // Will trigger tier3 discount (15%)
            50 // Initial stock
        );
        
        var productResponse = productService.createProduct(productRequest);
        productId = productResponse.getId();
    }

    @AfterEach
    void tearDown() {
        // Clean up for non-transactional tests
        if (productId != null) {
            productRepository.deleteById(productId);
        }
    }

    @Test
    void orderPlacementPipeline_FullFlow_Success() {
        // Given - Order request for 2 items
        OrderCreateRequest.OrderItemRequest itemRequest = new OrderCreateRequest.OrderItemRequest("INTEGRATION-SKU", 2);
        OrderCreateRequest orderRequest = new OrderCreateRequest("integration@test.com", List.of(itemRequest));

        // When - Create order
        OrderResponse orderResponse = orderService.createOrder(orderRequest, "integration-test-key");

        // Then - Verify order was created correctly
        assertNotNull(orderResponse);
        assertEquals("integration@test.com", orderResponse.getCustomerEmail());
        assertEquals("PENDING", orderResponse.getStatus());
        assertEquals(new BigDecimal("200.00"), orderResponse.getSubtotal()); // 2 * $100
        assertEquals(new BigDecimal("30.00"), orderResponse.getDiscountAmount()); // 15% of $200 (tier3)
        assertEquals(new BigDecimal("170.00"), orderResponse.getTotal()); // $200 - $30
        assertEquals(1, orderResponse.getItems().size());

        // Verify customer was created
        Optional<Customer> customer = customerRepository.findByEmail("integration@test.com");
        assertTrue(customer.isPresent());

        // Verify stock was decremented atomically
        Product product = productRepository.findById(productId).orElseThrow();
        assertEquals(48, product.getStockQuantity()); // 50 - 2 = 48

        // Verify order persisted in database
        OrderEntity persistedOrder = orderRepository.findById(orderResponse.getId()).orElseThrow();
        assertEquals(OrderEntity.OrderStatus.PENDING, persistedOrder.getStatus());
    }

    @Test
    void orderPlacementPipeline_IdempotencyKey_PreventsDuplicate() {
        // Given - Same idempotency key used twice
        OrderCreateRequest.OrderItemRequest itemRequest = new OrderCreateRequest.OrderItemRequest("INTEGRATION-SKU", 1);
        OrderCreateRequest orderRequest = new OrderCreateRequest("idempotency@test.com", List.of(itemRequest));
        String idempotencyKey = "duplicate-prevention-key";

        // When - Create order twice with same key
        OrderResponse firstResponse = orderService.createOrder(orderRequest, idempotencyKey);
        OrderResponse secondResponse = orderService.createOrder(orderRequest, idempotencyKey);

        // Then - Same order returned, no duplicate created
        assertEquals(firstResponse.getId(), secondResponse.getId());
        assertEquals(firstResponse.getTotal(), secondResponse.getTotal());

        // Verify stock only decremented once
        Product product = productRepository.findById(productId).orElseThrow();
        assertEquals(49, product.getStockQuantity()); // 50 - 1 = 49 (not 48)

        // Verify only one order exists
        List<OrderEntity> orders = orderRepository.findAll();
        long orderCount = orders.stream()
            .filter(order -> order.getIdempotencyKey() != null && order.getIdempotencyKey().equals(idempotencyKey))
            .count();
        assertEquals(1, orderCount);
    }

    @Test
    void orderCancellation_RestoresStock_Success() {
        // Given - Create an order first
        OrderCreateRequest.OrderItemRequest itemRequest = new OrderCreateRequest.OrderItemRequest("INTEGRATION-SKU", 3);
        OrderCreateRequest orderRequest = new OrderCreateRequest("cancellation@test.com", List.of(itemRequest));
        OrderResponse orderResponse = orderService.createOrder(orderRequest, "cancellation-key");

        // Verify initial stock decrement
        Product productBeforeCancel = productRepository.findById(productId).orElseThrow();
        assertEquals(47, productBeforeCancel.getStockQuantity()); // 50 - 3 = 47

        // When - Cancel the order
        OrderResponse cancelledResponse = orderService.cancelOrder(orderResponse.getId());

        // Then - Order marked as cancelled
        assertEquals("CANCELLED", cancelledResponse.getStatus());

        // Verify stock was restored
        Product productAfterCancel = productRepository.findById(productId).orElseThrow();
        assertEquals(50, productAfterCancel.getStockQuantity()); // 47 + 3 = 50 (restored)

        // Verify order status in database
        OrderEntity persistedOrder = orderRepository.findById(orderResponse.getId()).orElseThrow();
        assertEquals(OrderEntity.OrderStatus.CANCELLED, persistedOrder.getStatus());
    }

    @Test
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    void orderPlacement_InsufficientStock_RollsBackTransaction() {
        // Given - Product with limited stock
        Product product = productRepository.findById(productId).orElseThrow();
        product.setStockQuantity(1); // Only 1 item in stock
        productRepository.save(product);

        // Order request for more than available stock
        OrderCreateRequest.OrderItemRequest itemRequest = new OrderCreateRequest.OrderItemRequest("INTEGRATION-SKU", 5);
        OrderCreateRequest orderRequest = new OrderCreateRequest("insufficient@test.com", List.of(itemRequest));

        // When & Then - Order creation fails
        assertThrows(Exception.class, () -> {
            orderService.createOrder(orderRequest, "insufficient-stock-key");
        });

        // Verify no order was created
        Optional<Customer> customer = customerRepository.findByEmail("insufficient@test.com");
        assertFalse(customer.isPresent()); // Transaction rolled back

        // Verify stock unchanged
        Product productAfter = productRepository.findById(productId).orElseThrow();
        assertEquals(1, productAfter.getStockQuantity()); // Still 1, not decremented
    }
}