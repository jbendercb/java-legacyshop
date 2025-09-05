package com.example.legacyshop.dto;

import com.example.legacyshop.entity.Product;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * DTO for product responses.
 * 
 * Key patterns:
 * - Static factory method from entity
 * - Immutable response object
 * - Includes all relevant fields for API consumers
 */
public class ProductResponse {

    private final Long id;
    private final String sku;
    private final String name;
    private final String description;
    private final BigDecimal price;
    private final Integer stockQuantity;
    private final Boolean active;
    private final LocalDateTime createdAt;
    private final LocalDateTime updatedAt;

    // Constructor
    public ProductResponse(Long id, String sku, String name, String description, 
                          BigDecimal price, Integer stockQuantity, Boolean active,
                          LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.id = id;
        this.sku = sku;
        this.name = name;
        this.description = description;
        this.price = price;
        this.stockQuantity = stockQuantity;
        this.active = active;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    // Static factory method
    public static ProductResponse from(Product product) {
        return new ProductResponse(
            product.getId(),
            product.getSku(),
            product.getName(),
            product.getDescription(),
            product.getPrice(),
            product.getStockQuantity(),
            product.getActive(),
            product.getCreatedAt(),
            product.getUpdatedAt()
        );
    }

    // Getters
    public Long getId() { return id; }
    public String getSku() { return sku; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public BigDecimal getPrice() { return price; }
    public Integer getStockQuantity() { return stockQuantity; }
    public Boolean getActive() { return active; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}