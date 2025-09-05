package com.example.legacyshop.dto;

import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.entity.OrderItem;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * DTO for order responses.
 * 
 * Key patterns:
 * - Static factory method from entity
 * - Nested DTOs for order items
 * - Status enum exposure
 */
public class OrderResponse {

    private final Long id;
    private final String customerEmail;
    private final String status;
    private final BigDecimal subtotal;
    private final BigDecimal discountAmount;
    private final BigDecimal total;
    private final String idempotencyKey;
    private final List<OrderItemResponse> items;
    private final LocalDateTime createdAt;
    private final LocalDateTime updatedAt;

    // Constructor
    public OrderResponse(Long id, String customerEmail, String status, 
                        BigDecimal subtotal, BigDecimal discountAmount, BigDecimal total,
                        String idempotencyKey, List<OrderItemResponse> items,
                        LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.id = id;
        this.customerEmail = customerEmail;
        this.status = status;
        this.subtotal = subtotal;
        this.discountAmount = discountAmount;
        this.total = total;
        this.idempotencyKey = idempotencyKey;
        this.items = items;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    // Static factory method
    public static OrderResponse from(OrderEntity order) {
        List<OrderItemResponse> itemResponses = order.getItems().stream()
            .map(OrderItemResponse::from)
            .toList();

        return new OrderResponse(
            order.getId(),
            order.getCustomer().getEmail(),
            order.getStatus().name(),
            order.getSubtotal(),
            order.getDiscountAmount(),
            order.getTotal(),
            order.getIdempotencyKey(),
            itemResponses,
            order.getCreatedAt(),
            order.getUpdatedAt()
        );
    }

    // Getters
    public Long getId() { return id; }
    public String getCustomerEmail() { return customerEmail; }
    public String getStatus() { return status; }
    public BigDecimal getSubtotal() { return subtotal; }
    public BigDecimal getDiscountAmount() { return discountAmount; }
    public BigDecimal getTotal() { return total; }
    public String getIdempotencyKey() { return idempotencyKey; }
    public List<OrderItemResponse> getItems() { return items; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    /**
     * Nested DTO for order item responses.
     */
    public static class OrderItemResponse {
        
        private final Long id;
        private final String productSku;
        private final String productName;
        private final Integer quantity;
        private final BigDecimal unitPrice;
        private final BigDecimal subtotal;

        public OrderItemResponse(Long id, String productSku, String productName,
                               Integer quantity, BigDecimal unitPrice, BigDecimal subtotal) {
            this.id = id;
            this.productSku = productSku;
            this.productName = productName;
            this.quantity = quantity;
            this.unitPrice = unitPrice;
            this.subtotal = subtotal;
        }

        public static OrderItemResponse from(OrderItem item) {
            return new OrderItemResponse(
                item.getId(),
                item.getProductSku(),
                item.getProductName(),
                item.getQuantity(),
                item.getUnitPrice(),
                item.getSubtotal()
            );
        }

        // Getters
        public Long getId() { return id; }
        public String getProductSku() { return productSku; }
        public String getProductName() { return productName; }
        public Integer getQuantity() { return quantity; }
        public BigDecimal getUnitPrice() { return unitPrice; }
        public BigDecimal getSubtotal() { return subtotal; }
    }
}