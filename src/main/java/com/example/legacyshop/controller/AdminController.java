package com.example.legacyshop.controller;

import com.example.legacyshop.service.InventoryService;
import com.example.legacyshop.service.LoyaltyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Administrative endpoints for manual triggering of scheduled tasks.
 * 
 * Key patterns:
 * - Manual trigger endpoints for testing scheduled jobs
 * - Simple JSON responses for operational feedback
 * - Useful for development and testing
 */
@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final InventoryService inventoryService;
    private final LoyaltyService loyaltyService;

    public AdminController(InventoryService inventoryService, LoyaltyService loyaltyService) {
        this.inventoryService = inventoryService;
        this.loyaltyService = loyaltyService;
    }

    /**
     * Manually trigger inventory replenishment.
     * POST /api/admin/trigger-replenishment
     */
    @PostMapping("/trigger-replenishment")
    public ResponseEntity<?> triggerReplenishment() {
        try {
            inventoryService.triggerManualReplenishment();
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "Inventory replenishment completed successfully"
            ));
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                "status", "error",
                "message", "Replenishment failed: " + e.getMessage()
            ));
        }
    }

    /**
     * Manually trigger loyalty points processing.
     * POST /api/admin/trigger-loyalty-processing
     */
    @PostMapping("/trigger-loyalty-processing")
    public ResponseEntity<?> triggerLoyaltyProcessing() {
        try {
            int processed = loyaltyService.triggerManualLoyaltyProcessing();
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "Loyalty points processing completed",
                "ordersProcessed", processed
            ));
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                "status", "error",
                "message", "Loyalty processing failed: " + e.getMessage()
            ));
        }
    }

    /**
     * Replenish specific product.
     * POST /api/admin/replenish-product/{productId}?quantity=100
     */
    @PostMapping("/replenish-product/{productId}")
    public ResponseEntity<?> replenishProduct(
            @PathVariable Long productId, 
            @RequestParam(defaultValue = "100") int quantity) {
        try {
            inventoryService.replenishProduct(productId, quantity);
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", String.format("Product %d replenished with %d units", productId, quantity)
            ));
        } catch (Exception e) {
            return ResponseEntity.status(400).body(Map.of(
                "status", "error",
                "message", "Replenishment failed: " + e.getMessage()
            ));
        }
    }
}