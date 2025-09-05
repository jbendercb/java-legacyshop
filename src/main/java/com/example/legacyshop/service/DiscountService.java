package com.example.legacyshop.service;

import com.example.legacyshop.config.BusinessConfig;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Service for calculating discounts based on config-driven business rules.
 * 
 * Key patterns:
 * - Config-driven business logic
 * - Tiered discount calculation
 * - Immutable discount calculation
 */
@Service
public class DiscountService {

    private final BusinessConfig businessConfig;

    public DiscountService(BusinessConfig businessConfig) {
        this.businessConfig = businessConfig;
    }

    /**
     * Calculate discount amount based on order subtotal.
     * Uses tiered discount structure from configuration.
     */
    public BigDecimal calculateDiscount(BigDecimal subtotal) {
        if (subtotal == null) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }

        BusinessConfig.Promotions promotions = businessConfig.getPromotions();
        
        // Check highest tier first (tier3)
        if (subtotal.compareTo(promotions.getTier3().getThreshold()) >= 0) {
            return subtotal.multiply(promotions.getTier3().getDiscount())
                    .setScale(2, RoundingMode.HALF_UP);
        }
        
        // Check middle tier (tier2)
        if (subtotal.compareTo(promotions.getTier2().getThreshold()) >= 0) {
            return subtotal.multiply(promotions.getTier2().getDiscount())
                    .setScale(2, RoundingMode.HALF_UP);
        }
        
        // Check lowest tier (tier1)
        if (subtotal.compareTo(promotions.getTier1().getThreshold()) >= 0) {
            return subtotal.multiply(promotions.getTier1().getDiscount())
                    .setScale(2, RoundingMode.HALF_UP);
        }
        
        // No discount applicable
        return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * Get the discount rate (percentage) that would apply to the given subtotal.
     * Useful for displaying to customers.
     */
    public BigDecimal getDiscountRate(BigDecimal subtotal) {
        if (subtotal == null) {
            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
        }

        BusinessConfig.Promotions promotions = businessConfig.getPromotions();
        
        if (subtotal.compareTo(promotions.getTier3().getThreshold()) >= 0) {
            return promotions.getTier3().getDiscount().setScale(2, RoundingMode.HALF_UP);
        }
        
        if (subtotal.compareTo(promotions.getTier2().getThreshold()) >= 0) {
            return promotions.getTier2().getDiscount().setScale(2, RoundingMode.HALF_UP);
        }
        
        if (subtotal.compareTo(promotions.getTier1().getThreshold()) >= 0) {
            return promotions.getTier1().getDiscount().setScale(2, RoundingMode.HALF_UP);
        }
        
        return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);
    }
}