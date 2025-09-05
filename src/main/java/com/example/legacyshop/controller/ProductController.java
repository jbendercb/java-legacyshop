package com.example.legacyshop.controller;

import com.example.legacyshop.dto.ProductCreateRequest;
import com.example.legacyshop.dto.ProductResponse;
import com.example.legacyshop.dto.ProductUpdateRequest;
import com.example.legacyshop.service.ProductService;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller for Product CRUD operations.
 * 
 * Key patterns:
 * - RESTful resource design
 * - Bean validation with @Valid
 * - Pagination with Pageable
 * - Appropriate HTTP status codes
 * - Search functionality
 */
@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final ProductService productService;

    public ProductController(ProductService productService) {
        this.productService = productService;
    }

    /**
     * Create new product.
     * POST /api/products
     */
    @PostMapping
    public ResponseEntity<ProductResponse> createProduct(@Valid @RequestBody ProductCreateRequest request) {
        ProductResponse response = productService.createProduct(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Get product by ID.
     * GET /api/products/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> getProduct(@PathVariable Long id) {
        ProductResponse response = productService.getProduct(id);
        return ResponseEntity.ok(response);
    }

    /**
     * Get product by SKU.
     * GET /api/products/by-sku/{sku}
     */
    @GetMapping("/by-sku/{sku}")
    public ResponseEntity<ProductResponse> getProductBySku(@PathVariable String sku) {
        ProductResponse response = productService.getProductBySku(sku);
        return ResponseEntity.ok(response);
    }

    /**
     * Get all active products with pagination.
     * GET /api/products?page=0&size=20&sort=name,asc
     */
    @GetMapping
    public ResponseEntity<Page<ProductResponse>> getProducts(
            @PageableDefault(size = 20, sort = "name") Pageable pageable) {
        Page<ProductResponse> response = productService.getActiveProducts(pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * Search products by name with pagination.
     * GET /api/products/search?name=laptop&page=0&size=20
     */
    @GetMapping("/search")
    public ResponseEntity<Page<ProductResponse>> searchProducts(
            @RequestParam String name,
            @PageableDefault(size = 20, sort = "name") Pageable pageable) {
        Page<ProductResponse> response = productService.searchProducts(name, pageable);
        return ResponseEntity.ok(response);
    }

    /**
     * Update product.
     * PUT /api/products/{id}
     */
    @PutMapping("/{id}")
    public ResponseEntity<ProductResponse> updateProduct(
            @PathVariable Long id,
            @Valid @RequestBody ProductUpdateRequest request) {
        ProductResponse response = productService.updateProduct(id, request);
        return ResponseEntity.ok(response);
    }

    /**
     * Soft delete product.
     * DELETE /api/products/{id}
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
        productService.deleteProduct(id);
        return ResponseEntity.noContent().build();
    }
}