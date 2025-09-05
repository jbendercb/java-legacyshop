package com.example.legacyshop.service;

import com.example.legacyshop.dto.OrderCreateRequest;
import com.example.legacyshop.dto.OrderResponse;
import com.example.legacyshop.entity.*;
import com.example.legacyshop.exception.BusinessValidationException;
import com.example.legacyshop.exception.ResourceNotFoundException;
import com.example.legacyshop.repository.*;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Optional;

/**
 * Service for Order operations demonstrating the complete order placement pipeline.
 * 
 * Key patterns demonstrated:
 * 1. Atomic transaction boundary
 * 2. Validation → Stock Check → Price Calculation → Persist → Stock Decrement
 * 3. Rollback on any failure
 * 4. Idempotency support
 * 5. Business rule enforcement
 */
@Service
@Transactional(readOnly = true)
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final CustomerRepository customerRepository;
    private final AuditLogRepository auditLogRepository;
    private final IdempotencyRecordRepository idempotencyRecordRepository;
    private final CustomerService customerService;
    private final DiscountService discountService;
    private final PaymentService paymentService;

    public OrderService(OrderRepository orderRepository,
                       ProductRepository productRepository,
                       CustomerRepository customerRepository,
                       AuditLogRepository auditLogRepository,
                       IdempotencyRecordRepository idempotencyRecordRepository,
                       CustomerService customerService,
                       DiscountService discountService,
                       PaymentService paymentService) {
        this.orderRepository = orderRepository;
        this.productRepository = productRepository;
        this.customerRepository = customerRepository;
        this.auditLogRepository = auditLogRepository;
        this.idempotencyRecordRepository = idempotencyRecordRepository;
        this.customerService = customerService;
        this.discountService = discountService;
        this.paymentService = paymentService;
    }

    /**
     * Create order with complete pipeline: validate → stock check → price → persist → decrement stock.
     * Demonstrates atomic rollback on any failure.
     */
    @Transactional
    public OrderResponse createOrder(OrderCreateRequest request, String idempotencyKey) {
        // Step 1: Check for idempotency (prevent duplicates)
        if (idempotencyKey != null) {
            Optional<OrderEntity> existingOrder = orderRepository.findByIdempotencyKey(idempotencyKey);
            if (existingOrder.isPresent()) {
                return OrderResponse.from(existingOrder.get());
            }
        }

        // Step 2: Validate customer (find or create)
        Customer customer = customerService.findOrCreateCustomer(
            request.getCustomerEmail(),
            extractFirstName(request.getCustomerEmail()),
            extractLastName(request.getCustomerEmail())
        );

        // Step 3: Create order entity
        OrderEntity order = new OrderEntity(customer, idempotencyKey);

        // Step 4: Process each line item with validation and stock checks
        for (OrderCreateRequest.OrderItemRequest itemRequest : request.getItems()) {
            processOrderItem(order, itemRequest);
        }

        // Step 5: Calculate totals and apply discounts
        order.calculateTotals();
        BigDecimal discountAmount = discountService.calculateDiscount(order.getSubtotal());
        order.applyDiscount(discountAmount);

        // Step 6: Validate minimum order total
        if (order.getTotal().compareTo(new BigDecimal("0.01")) < 0) {
            throw new BusinessValidationException("Order total must be at least $0.01");
        }

        // Step 7: Persist order
        OrderEntity savedOrder = orderRepository.save(order);

        // Step 8: Record idempotency (if provided)
        if (idempotencyKey != null) {
            IdempotencyRecord record = new IdempotencyRecord(idempotencyKey, "ORDER_CREATE");
            record.setResult(savedOrder.getId(), savedOrder.getStatus().name());
            idempotencyRecordRepository.save(record);
        }

        // Step 9: Create audit log
        AuditLog auditLog = AuditLog.orderCreatedLog(savedOrder.getId(), customer.getEmail());
        auditLogRepository.save(auditLog);

        return OrderResponse.from(savedOrder);
    }

    /**
     * Process individual order item with validation and atomic stock decrement.
     */
    private void processOrderItem(OrderEntity order, OrderCreateRequest.OrderItemRequest itemRequest) {
        // Find product by SKU
        Product product = productRepository.findBySku(itemRequest.getProductSku())
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with SKU: " + itemRequest.getProductSku()));

        // Validate product is active
        if (!product.getActive()) {
            throw new BusinessValidationException("Product " + product.getSku() + " is not available");
        }

        // Check stock availability BEFORE decrementing
        if (product.getStockQuantity() < itemRequest.getQuantity()) {
            throw new BusinessValidationException(
                String.format("Insufficient stock for product %s. Available: %d, Requested: %d",
                    product.getSku(), product.getStockQuantity(), itemRequest.getQuantity())
            );
        }

        // Capture current price (price at order time, not derived)
        BigDecimal unitPrice = product.getPrice();

        // Create order item
        OrderItem orderItem = new OrderItem(order, product, itemRequest.getQuantity(), unitPrice);
        order.addItem(orderItem);

        // ATOMIC OPERATION: Decrement stock
        // This is the critical part - if this fails, entire transaction rolls back
        product.decrementStock(itemRequest.getQuantity());
        productRepository.save(product);
    }

    /**
     * Get order by ID.
     */
    public OrderResponse getOrder(Long id) {
        OrderEntity order = orderRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + id));
        return OrderResponse.from(order);
    }

    /**
     * Get orders for customer with pagination.
     */
    public Page<OrderResponse> getCustomerOrders(String email, Pageable pageable) {
        Customer customer = customerService.findByEmail(email);
        return orderRepository.findByCustomerId(customer.getId(), pageable)
            .map(OrderResponse::from);
    }

    /**
     * Cancel order with compensating actions (restore stock, void payment).
     */
    @Transactional
    public OrderResponse cancelOrder(Long orderId) {
        OrderEntity order = orderRepository.findById(orderId)
            .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + orderId));

        if (!order.canBeCancelled()) {
            throw new BusinessValidationException("Order cannot be cancelled in status: " + order.getStatus());
        }

        // Compensating action 1: Restore stock for all items
        for (OrderItem item : order.getItems()) {
            Product product = item.getProduct();
            product.incrementStock(item.getQuantity());
            productRepository.save(product);
        }

        // Compensating action 2: Void payment if exists
        if (order.getPayment() != null && order.getPayment().getStatus() == Payment.PaymentStatus.AUTHORIZED) {
            paymentService.voidPayment(order.getPayment().getId());
        }

        // Update order status
        order.cancel();
        OrderEntity savedOrder = orderRepository.save(order);

        // Audit logging
        AuditLog auditLog = AuditLog.orderCancelledLog(savedOrder.getId(), "Customer requested cancellation");
        auditLogRepository.save(auditLog);

        return OrderResponse.from(savedOrder);
    }

    // Helper methods for customer name extraction (simplified)
    private String extractFirstName(String email) {
        String localPart = email.substring(0, email.indexOf('@'));
        return localPart.replaceAll("[^a-zA-Z]", "");
    }

    private String extractLastName(String email) {
        return "Customer"; // Simplified - in real app might extract from email or require in request
    }
}