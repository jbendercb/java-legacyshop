package com.example.legacyshop.controller;

import com.example.legacyshop.dto.OrderCreateRequest;
import com.example.legacyshop.dto.OrderResponse;
import com.example.legacyshop.entity.IdempotencyRecord;
import com.example.legacyshop.repository.IdempotencyRecordRepository;
import com.example.legacyshop.service.OrderService;
import com.example.legacyshop.service.PaymentService;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

/**
 * REST controller for Order operations.
 * 
 * Key patterns:
 * - Idempotency via Idempotency-Key header
 * - Order placement pipeline
 * - Payment authorization integration
 * - Order cancellation with compensation
 */
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private final OrderService orderService;
    private final PaymentService paymentService;
    private final IdempotencyRecordRepository idempotencyRecordRepository;

    public OrderController(OrderService orderService, PaymentService paymentService, 
                          IdempotencyRecordRepository idempotencyRecordRepository) {
        this.orderService = orderService;
        this.paymentService = paymentService;
        this.idempotencyRecordRepository = idempotencyRecordRepository;
    }

    /**
     * Create order with idempotency support.
     * POST /api/orders
     * Header: Idempotency-Key: unique-key-per-request
     */
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody OrderCreateRequest request,
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey) {
        
        // If idempotency key is provided, check for existing order
        if (idempotencyKey != null && !idempotencyKey.trim().isEmpty()) {
            Optional<IdempotencyRecord> existingRecord = idempotencyRecordRepository.findByIdempotencyKey(idempotencyKey);
            if (existingRecord.isPresent() && existingRecord.get().getResultEntityId() != null) {
                // Return existing order
                OrderResponse existingOrder = orderService.getOrder(existingRecord.get().getResultEntityId());
                return ResponseEntity.ok(existingOrder);
            }
        }
        
        OrderResponse response = orderService.createOrder(request, idempotencyKey);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Get order by ID.
     * GET /api/orders/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<OrderResponse> getOrder(@PathVariable Long id) {
        OrderResponse response = orderService.getOrder(id);
        return ResponseEntity.ok(response);
    }

    /**
     * Get orders for customer with pagination.
     * GET /api/orders/customer/{email}?page=0&size=10
     */
    @GetMapping("/customer/{email}")
    public ResponseEntity<Page<OrderResponse>> getCustomerOrders(
            @PathVariable String email,
            @PageableDefault(size = 10, sort = "createdAt") Pageable pageable) {
        
        Page<OrderResponse> response = orderService.getCustomerOrders(email, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * Authorize payment for order.
     * POST /api/orders/{id}/authorize-payment
     */
    @PostMapping("/{id}/authorize-payment")
    public ResponseEntity<?> authorizePayment(@PathVariable Long id) {
        try {
            paymentService.authorizePayment(id);
            return ResponseEntity.ok().body("{\"status\": \"Payment authorized successfully\"}");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                .body("{\"error\": \"Payment authorization failed: " + e.getMessage() + "\"}");
        }
    }

    /**
     * Cancel order with compensating actions.
     * POST /api/orders/{id}/cancel
     */
    @PostMapping("/{id}/cancel")
    public ResponseEntity<OrderResponse> cancelOrder(@PathVariable Long id) {
        OrderResponse response = orderService.cancelOrder(id);
        return ResponseEntity.ok(response);
    }
}