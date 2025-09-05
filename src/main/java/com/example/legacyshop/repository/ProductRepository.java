package com.example.legacyshop.repository;

import com.example.legacyshop.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository for Product entity operations.
 * 
 * Key patterns demonstrated:
 * - Custom query methods with naming conventions
 * - Optional return types for null safety
 * - Pagination support
 * - Custom JPQL queries where needed
 */
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    /**
     * Find product by SKU (used for uniqueness validation).
     */
    Optional<Product> findBySku(String sku);

    /**
     * Check if SKU exists (for validation without loading entity).
     */
    boolean existsBySku(String sku);

    /**
     * Find active products only.
     */
    Page<Product> findByActiveTrue(Pageable pageable);

    /**
     * Find products with stock below threshold (for replenishment).
     */
    @Query("SELECT p FROM Product p WHERE p.active = true AND p.stockQuantity < :threshold")
    Page<Product> findProductsNeedingReplenishment(int threshold, Pageable pageable);

    /**
     * Find products by name containing text (case insensitive).
     */
    Page<Product> findByNameContainingIgnoreCase(String name, Pageable pageable);
}