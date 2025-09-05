package com.example.legacyshop.service;

import com.example.legacyshop.config.BusinessConfig;
import com.example.legacyshop.entity.AuditLog;
import com.example.legacyshop.entity.Product;
import com.example.legacyshop.repository.AuditLogRepository;
import com.example.legacyshop.repository.ProductRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service for inventory management and scheduled replenishment.
 * 
 * Key patterns:
 * - @Scheduled annotation for nightly jobs
 * - Batch processing with pagination
 * - Audit logging for business operations
 * - Config-driven thresholds and quantities
 */
@Service
public class InventoryService {

    private static final Logger logger = LoggerFactory.getLogger(InventoryService.class);

    private final ProductRepository productRepository;
    private final AuditLogRepository auditLogRepository;
    private final BusinessConfig businessConfig;

    public InventoryService(ProductRepository productRepository, 
                           AuditLogRepository auditLogRepository,
                           BusinessConfig businessConfig) {
        this.productRepository = productRepository;
        this.auditLogRepository = auditLogRepository;
        this.businessConfig = businessConfig;
    }

    /**
     * Nightly scheduled inventory replenishment.
     * Runs at 2 AM every night to restock products with low inventory.
     * 
     * Cron expression: second minute hour day-of-month month day-of-week
     * "0 0 2 * * ?" = At 2:00 AM every day
     */
    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional
    public void performNightlyReplenishment() {
        logger.info("Starting nightly inventory replenishment");
        
        int threshold = 10; // Restock products with less than 10 units
        int restockQuantity = businessConfig.getInventory().getDefaultRestockQuantity();
        int totalReplenished = 0;
        
        try {
            // Process in batches to handle large inventories
            Pageable pageable = PageRequest.of(0, 50); // 50 products per batch
            Page<Product> productsPage;
            
            do {
                productsPage = productRepository.findProductsNeedingReplenishment(threshold, pageable);
                
                for (Product product : productsPage.getContent()) {
                    replenishProduct(product, restockQuantity);
                    totalReplenished++;
                }
                
                // Move to next page
                pageable = productsPage.nextPageable();
                
            } while (productsPage.hasNext());
            
            // Create summary audit log
            AuditLog summaryLog = new AuditLog(
                AuditLog.OperationType.INVENTORY_REPLENISHMENT,
                "System",
                null,
                String.format("Nightly replenishment completed. %d products restocked with %d units each", 
                             totalReplenished, restockQuantity)
            );
            auditLogRepository.save(summaryLog);
            
            logger.info("Nightly inventory replenishment completed. Restocked {} products", totalReplenished);
            
        } catch (Exception e) {
            logger.error("Error during nightly inventory replenishment", e);
            
            // Create error audit log
            AuditLog errorLog = new AuditLog(
                AuditLog.OperationType.INVENTORY_REPLENISHMENT,
                "System",
                null,
                "Nightly replenishment failed: " + e.getMessage()
            );
            auditLogRepository.save(errorLog);
        }
    }

    /**
     * Manual inventory replenishment for specific product.
     */
    @Transactional
    public void replenishProduct(Long productId, int quantity) {
        Product product = productRepository.findById(productId)
            .orElseThrow(() -> new IllegalArgumentException("Product not found: " + productId));
        
        replenishProduct(product, quantity);
    }

    /**
     * Internal method to replenish a single product.
     */
    private void replenishProduct(Product product, int quantity) {
        int previousStock = product.getStockQuantity();
        product.incrementStock(quantity);
        productRepository.save(product);
        
        // Individual product audit log
        AuditLog auditLog = AuditLog.replenishmentLog(
            product.getId(),
            product.getSku(),
            quantity
        );
        auditLog.setDetails(
            String.format("Restocked product %s from %d to %d units (+%d)", 
                         product.getSku(), previousStock, product.getStockQuantity(), quantity)
        );
        auditLogRepository.save(auditLog);
        
        logger.debug("Replenished product {} from {} to {} units", 
                    product.getSku(), previousStock, product.getStockQuantity());
    }

    /**
     * Manual trigger for replenishment (useful for testing).
     */
    @Transactional
    public void triggerManualReplenishment() {
        logger.info("Manual replenishment triggered");
        performNightlyReplenishment();
    }

    /**
     * Get inventory report showing products with low stock.
     */
    @Transactional(readOnly = true)
    public Page<Product> getLowStockProducts(int threshold, Pageable pageable) {
        return productRepository.findProductsNeedingReplenishment(threshold, pageable);
    }
}