package com.example.legacyshop.service;

import com.example.legacyshop.dto.ProductCreateRequest;
import com.example.legacyshop.dto.ProductResponse;
import com.example.legacyshop.dto.ProductUpdateRequest;
import com.example.legacyshop.entity.AuditLog;
import com.example.legacyshop.entity.Product;
import com.example.legacyshop.exception.DuplicateResourceException;
import com.example.legacyshop.exception.ResourceNotFoundException;
import com.example.legacyshop.repository.AuditLogRepository;
import com.example.legacyshop.repository.ProductRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service for Product CRUD operations with business validation.
 * 
 * Key patterns:
 * - SKU uniqueness validation
 * - Transactional boundaries
 * - Audit logging for business events
 * - DTO to entity conversion
 * - Custom business exceptions
 */
@Service
@Transactional(readOnly = true)
public class ProductService {

    private final ProductRepository productRepository;
    private final AuditLogRepository auditLogRepository;

    public ProductService(ProductRepository productRepository, AuditLogRepository auditLogRepository) {
        this.productRepository = productRepository;
        this.auditLogRepository = auditLogRepository;
    }

    /**
     * Create new product with SKU uniqueness validation.
     */
    @Transactional
    public ProductResponse createProduct(ProductCreateRequest request) {
        // Business rule: SKU must be unique
        if (productRepository.existsBySku(request.getSku())) {
            throw new DuplicateResourceException("Product with SKU '" + request.getSku() + "' already exists");
        }

        Product product = new Product(
            request.getSku(),
            request.getName(),
            request.getDescription(),
            request.getPrice(),
            request.getStockQuantity()
        );

        Product saved = productRepository.save(product);
        
        // Audit logging
        AuditLog auditLog = new AuditLog(
            AuditLog.OperationType.PRODUCT_CREATED,
            "Product",
            saved.getId(),
            "Created product with SKU: " + saved.getSku()
        );
        auditLogRepository.save(auditLog);

        return ProductResponse.from(saved);
    }

    /**
     * Update existing product.
     */
    @Transactional
    public ProductResponse updateProduct(Long id, ProductUpdateRequest request) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));

        // Update only non-null fields (partial update pattern)
        if (request.getName() != null) {
            product.setName(request.getName());
        }
        if (request.getDescription() != null) {
            product.setDescription(request.getDescription());
        }
        if (request.getPrice() != null) {
            product.setPrice(request.getPrice());
        }
        if (request.getStockQuantity() != null) {
            product.setStockQuantity(request.getStockQuantity());
        }
        if (request.getActive() != null) {
            product.setActive(request.getActive());
        }

        Product saved = productRepository.save(product);

        // Audit logging
        AuditLog auditLog = new AuditLog(
            AuditLog.OperationType.PRODUCT_UPDATED,
            "Product",
            saved.getId(),
            "Updated product with SKU: " + saved.getSku()
        );
        auditLogRepository.save(auditLog);

        return ProductResponse.from(saved);
    }

    /**
     * Get product by ID.
     */
    public ProductResponse getProduct(Long id) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        return ProductResponse.from(product);
    }

    /**
     * Get product by SKU.
     */
    public ProductResponse getProductBySku(String sku) {
        Product product = productRepository.findBySku(sku)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with SKU: " + sku));
        return ProductResponse.from(product);
    }

    /**
     * Get all active products with pagination.
     */
    public Page<ProductResponse> getActiveProducts(Pageable pageable) {
        return productRepository.findByActiveTrue(pageable)
            .map(ProductResponse::from);
    }

    /**
     * Search products by name with pagination.
     */
    public Page<ProductResponse> searchProducts(String name, Pageable pageable) {
        return productRepository.findByNameContainingIgnoreCase(name, pageable)
            .map(ProductResponse::from);
    }

    /**
     * Soft delete product (set active = false).
     */
    @Transactional
    public void deleteProduct(Long id) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        
        product.setActive(false);
        productRepository.save(product);

        // Audit logging
        AuditLog auditLog = new AuditLog(
            AuditLog.OperationType.PRODUCT_UPDATED,
            "Product",
            product.getId(),
            "Deactivated product with SKU: " + product.getSku()
        );
        auditLogRepository.save(auditLog);
    }

    /**
     * Internal method for order processing - decrement stock atomically.
     */
    @Transactional
    public void decrementStock(Long productId, int quantity) {
        Product product = productRepository.findById(productId)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + productId));
        
        if (product.getStockQuantity() < quantity) {
            throw new IllegalStateException("Insufficient stock for product " + product.getSku() + 
                                          ". Available: " + product.getStockQuantity() + ", Requested: " + quantity);
        }

        product.decrementStock(quantity);
        productRepository.save(product);
    }

    /**
     * Internal method for order cancellation - increment stock (compensation).
     */
    @Transactional
    public void incrementStock(Long productId, int quantity) {
        Product product = productRepository.findById(productId)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + productId));
        
        product.incrementStock(quantity);
        productRepository.save(product);
    }
}