package com.example.legacyshop.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;

/**
 * DTO for creating new orders.
 * 
 * Key patterns:
 * - Nested validation with @Valid
 * - Customer identification by email
 * - Line item validation
 */
public class OrderCreateRequest {

    @NotBlank(message = "Customer email is required")
    @Email(message = "Customer email should be valid")
    private String customerEmail;

    @NotEmpty(message = "Order must have at least one item")
    @Valid
    private List<OrderItemRequest> items;

    // Constructors
    public OrderCreateRequest() {}

    public OrderCreateRequest(String customerEmail, List<OrderItemRequest> items) {
        this.customerEmail = customerEmail;
        this.items = items;
    }

    // Getters and Setters
    public String getCustomerEmail() { return customerEmail; }
    public void setCustomerEmail(String customerEmail) { this.customerEmail = customerEmail; }

    public List<OrderItemRequest> getItems() { return items; }
    public void setItems(List<OrderItemRequest> items) { this.items = items; }

    /**
     * Nested DTO for order items.
     */
    public static class OrderItemRequest {
        
        @NotBlank(message = "Product SKU is required")
        private String productSku;

        @NotNull(message = "Quantity is required")
        @Min(value = 1, message = "Quantity must be at least 1")
        private Integer quantity;

        // Constructors
        public OrderItemRequest() {}

        public OrderItemRequest(String productSku, Integer quantity) {
            this.productSku = productSku;
            this.quantity = quantity;
        }

        // Getters and Setters
        public String getProductSku() { return productSku; }
        public void setProductSku(String productSku) { this.productSku = productSku; }

        public Integer getQuantity() { return quantity; }
        public void setQuantity(Integer quantity) { this.quantity = quantity; }
    }
}