package com.example.legacyshop.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Order entity (named OrderEntity to avoid conflict with SQL ORDER keyword).
 * 
 * Key patterns:
 * - Order status workflow (PENDING -> PAID -> SHIPPED, or CANCELLED)
 * - One-to-many with OrderItem (cascade operations)
 * - Idempotency key for duplicate prevention
 * - Calculated totals with discount application
 */
@Entity
@Table(name = "orders",
       uniqueConstraints = @UniqueConstraint(name = "uk_order_idempotency_key", columnNames = "idempotencyKey"))
public class OrderEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OrderStatus status = OrderStatus.PENDING;

    @Size(max = 100, message = "Idempotency key must not exceed 100 characters")
    @Column(length = 100, unique = true)
    private String idempotencyKey;

    @NotNull(message = "Subtotal is required")
    @DecimalMin(value = "0.00", message = "Subtotal must be non-negative")
    @Digits(integer = 10, fraction = 2)
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal subtotal;

    @NotNull(message = "Discount amount is required")
    @DecimalMin(value = "0.00", message = "Discount amount must be non-negative")
    @Digits(integer = 10, fraction = 2)
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal discountAmount = BigDecimal.ZERO;

    @NotNull(message = "Total is required")
    @DecimalMin(value = "0.01", message = "Total must be at least 0.01")
    @Digits(integer = 10, fraction = 2)
    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal total;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<OrderItem> items = new ArrayList<>();

    @OneToOne(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Payment payment;

    // Audit fields
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Version
    private Long version;

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    // Constructors
    public OrderEntity() {}

    public OrderEntity(Customer customer, String idempotencyKey) {
        this.customer = customer;
        this.idempotencyKey = idempotencyKey;
    }

    // Business methods
    public void addItem(OrderItem item) {
        items.add(item);
        item.setOrder(this);
    }

    public void calculateTotals() {
        subtotal = items.stream()
                .map(OrderItem::getSubtotal)
                .filter(s -> s != null)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
        
        total = subtotal.subtract(discountAmount)
                .setScale(2, RoundingMode.HALF_UP);
    }

    public void applyDiscount(BigDecimal discountAmount) {
        this.discountAmount = discountAmount.setScale(2, RoundingMode.HALF_UP);
        calculateTotals();
    }

    public boolean canBeCancelled() {
        return status == OrderStatus.PENDING || status == OrderStatus.PAID;
    }

    public void cancel() {
        if (!canBeCancelled()) {
            throw new IllegalStateException("Order cannot be cancelled in status: " + status);
        }
        this.status = OrderStatus.CANCELLED;
    }

    public void markAsPaid() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Order must be PENDING to mark as PAID");
        }
        this.status = OrderStatus.PAID;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Customer getCustomer() { return customer; }
    public void setCustomer(Customer customer) { this.customer = customer; }

    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) { this.status = status; }

    public String getIdempotencyKey() { return idempotencyKey; }
    public void setIdempotencyKey(String idempotencyKey) { this.idempotencyKey = idempotencyKey; }

    public BigDecimal getSubtotal() { return subtotal; }
    public void setSubtotal(BigDecimal subtotal) { this.subtotal = subtotal; }

    public BigDecimal getDiscountAmount() { return discountAmount; }
    public void setDiscountAmount(BigDecimal discountAmount) { this.discountAmount = discountAmount; }

    public BigDecimal getTotal() { return total; }
    public void setTotal(BigDecimal total) { this.total = total; }

    public List<OrderItem> getItems() { return items; }
    public void setItems(List<OrderItem> items) { this.items = items; }

    public Payment getPayment() { return payment; }
    public void setPayment(Payment payment) { this.payment = payment; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }

    // Enums
    public enum OrderStatus {
        PENDING,    // Order created, awaiting payment
        PAID,       // Payment successful, can fulfill
        SHIPPED,    // Order shipped to customer
        CANCELLED   // Order cancelled, compensating actions applied
    }
}