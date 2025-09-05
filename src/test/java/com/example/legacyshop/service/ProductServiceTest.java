package com.example.legacyshop.service;

import com.example.legacyshop.dto.ProductCreateRequest;
import com.example.legacyshop.dto.ProductResponse;
import com.example.legacyshop.dto.ProductUpdateRequest;
import com.example.legacyshop.entity.Product;
import com.example.legacyshop.exception.DuplicateResourceException;
import com.example.legacyshop.exception.ResourceNotFoundException;
import com.example.legacyshop.repository.AuditLogRepository;
import com.example.legacyshop.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for ProductService focusing on business rules.
 * 
 * Tests cover:
 * - SKU uniqueness validation
 * - Product creation and updates
 * - Stock management operations
 * - Error handling scenarios
 */
@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private AuditLogRepository auditLogRepository;

    @InjectMocks
    private ProductService productService;

    private ProductCreateRequest createRequest;
    private Product product;

    @BeforeEach
    void setUp() {
        createRequest = new ProductCreateRequest(
            "TEST-SKU-001",
            "Test Product",
            "Test Description",
            new BigDecimal("99.99"),
            100
        );

        product = new Product(
            "TEST-SKU-001",
            "Test Product",
            "Test Description",
            new BigDecimal("99.99"),
            100
        );
        product.setId(1L);
    }

    @Test
    void createProduct_Success() {
        // Given
        when(productRepository.existsBySku("TEST-SKU-001")).thenReturn(false);
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        ProductResponse response = productService.createProduct(createRequest);

        // Then
        assertNotNull(response);
        assertEquals("TEST-SKU-001", response.getSku());
        assertEquals("Test Product", response.getName());
        assertEquals(new BigDecimal("99.99"), response.getPrice());
        assertEquals(100, response.getStockQuantity());

        verify(productRepository).existsBySku("TEST-SKU-001");
        verify(productRepository).save(any(Product.class));
        verify(auditLogRepository).save(any());
    }

    @Test
    void createProduct_DuplicateSku_ThrowsException() {
        // Given
        when(productRepository.existsBySku("TEST-SKU-001")).thenReturn(true);

        // When & Then
        DuplicateResourceException exception = assertThrows(
            DuplicateResourceException.class,
            () -> productService.createProduct(createRequest)
        );

        assertEquals("Product with SKU 'TEST-SKU-001' already exists", exception.getMessage());
        verify(productRepository).existsBySku("TEST-SKU-001");
        verify(productRepository, never()).save(any());
    }

    @Test
    void updateProduct_Success() {
        // Given
        ProductUpdateRequest updateRequest = new ProductUpdateRequest();
        updateRequest.setName("Updated Product");
        updateRequest.setPrice(new BigDecimal("149.99"));

        when(productRepository.findById(1L)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        ProductResponse response = productService.updateProduct(1L, updateRequest);

        // Then
        assertNotNull(response);
        verify(productRepository).findById(1L);
        verify(productRepository).save(any(Product.class));
        verify(auditLogRepository).save(any());
    }

    @Test
    void updateProduct_NotFound_ThrowsException() {
        // Given
        ProductUpdateRequest updateRequest = new ProductUpdateRequest();
        updateRequest.setName("Updated Product");

        when(productRepository.findById(1L)).thenReturn(Optional.empty());

        // When & Then
        ResourceNotFoundException exception = assertThrows(
            ResourceNotFoundException.class,
            () -> productService.updateProduct(1L, updateRequest)
        );

        assertEquals("Product not found with id: 1", exception.getMessage());
        verify(productRepository).findById(1L);
        verify(productRepository, never()).save(any());
    }

    @Test
    void decrementStock_Success() {
        // Given
        when(productRepository.findById(1L)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        productService.decrementStock(1L, 50);

        // Then
        verify(productRepository).findById(1L);
        verify(productRepository).save(any(Product.class));
        assertEquals(50, product.getStockQuantity());
    }

    @Test
    void decrementStock_InsufficientStock_ThrowsException() {
        // Given
        when(productRepository.findById(1L)).thenReturn(Optional.of(product));

        // When & Then
        IllegalStateException exception = assertThrows(
            IllegalStateException.class,
            () -> productService.decrementStock(1L, 150)
        );

        assertTrue(exception.getMessage().contains("Insufficient stock"));
        verify(productRepository).findById(1L);
        verify(productRepository, never()).save(any());
    }

    @Test
    void incrementStock_Success() {
        // Given
        when(productRepository.findById(1L)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        productService.incrementStock(1L, 50);

        // Then
        verify(productRepository).findById(1L);
        verify(productRepository).save(any(Product.class));
        assertEquals(150, product.getStockQuantity());
    }
}