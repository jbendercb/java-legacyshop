package com.example.legacyshop.dto;

import com.example.legacyshop.entity.OrderEntity;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * DTO for order reporting with optimized data structure.
 * 
 * Key patterns:
 * - Flattened structure to avoid N+1 queries
 * - Essential fields only for reporting
 * - Customer info included to prevent additional queries
 */
public class OrderReportResponse {

    private final Long orderId;
    private final String customerEmail;
    private final String customerName;
    private final String status;
    private final BigDecimal subtotal;
    private final BigDecimal discountAmount;
    private final BigDecimal total;
    private final int itemCount;
    private final LocalDateTime createdAt;
    private final String paymentStatus;

    public OrderReportResponse(Long orderId, String customerEmail, String customerName,
                              String status, BigDecimal subtotal, BigDecimal discountAmount,
                              BigDecimal total, int itemCount, LocalDateTime createdAt,
                              String paymentStatus) {
        this.orderId = orderId;
        this.customerEmail = customerEmail;
        this.customerName = customerName;
        this.status = status;
        this.subtotal = subtotal;
        this.discountAmount = discountAmount;
        this.total = total;
        this.itemCount = itemCount;
        this.createdAt = createdAt;
        this.paymentStatus = paymentStatus;
    }

    /**
     * Static factory method from entity with N+1 prevention.
     * Assumes entity has been fetched with necessary joins.
     */
    public static OrderReportResponse from(OrderEntity order) {
        String paymentStatus = order.getPayment() != null 
            ? order.getPayment().getStatus().name() 
            : "NO_PAYMENT";

        return new OrderReportResponse(
            order.getId(),
            order.getCustomer().getEmail(),
            order.getCustomer().getFullName(),
            order.getStatus().name(),
            order.getSubtotal(),
            order.getDiscountAmount(),
            order.getTotal(),
            order.getItems().size(),
            order.getCreatedAt(),
            paymentStatus
        );
    }

    // Getters
    public Long getOrderId() { return orderId; }
    public String getCustomerEmail() { return customerEmail; }
    public String getCustomerName() { return customerName; }
    public String getStatus() { return status; }
    public BigDecimal getSubtotal() { return subtotal; }
    public BigDecimal getDiscountAmount() { return discountAmount; }
    public BigDecimal getTotal() { return total; }
    public int getItemCount() { return itemCount; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public String getPaymentStatus() { return paymentStatus; }
}