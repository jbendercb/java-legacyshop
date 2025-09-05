package com.example.legacyshop.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

/**
 * DTO for updating existing products.
 * 
 * Key patterns:
 * - Similar to create request but SKU is not changeable
 * - All fields optional to support partial updates
 */
public class ProductUpdateRequest {

    @Size(max = 255, message = "Name must not exceed 255 characters")
    private String name;

    @Size(max = 1000, message = "Description must not exceed 1000 characters")
    private String description;

    @DecimalMin(value = "0.01", message = "Price must be at least 0.01")
    @Digits(integer = 10, fraction = 2, message = "Price must have at most 10 integer digits and 2 decimal places")
    private BigDecimal price;

    @Min(value = 0, message = "Stock quantity cannot be negative")
    private Integer stockQuantity;

    private Boolean active;

    // Constructors
    public ProductUpdateRequest() {}

    // Getters and Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public BigDecimal getPrice() { return price; }
    public void setPrice(BigDecimal price) { this.price = price; }

    public Integer getStockQuantity() { return stockQuantity; }
    public void setStockQuantity(Integer stockQuantity) { this.stockQuantity = stockQuantity; }

    public Boolean getActive() { return active; }
    public void setActive(Boolean active) { this.active = active; }
}