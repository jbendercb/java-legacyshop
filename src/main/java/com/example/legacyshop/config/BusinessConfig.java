package com.example.legacyshop.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.math.BigDecimal;

/**
 * Configuration properties for business rules.
 * 
 * Key patterns:
 * - Externalized configuration
 * - Type-safe configuration binding
 * - Nested configuration classes
 */
@Configuration
@ConfigurationProperties(prefix = "business")
public class BusinessConfig {

    private Promotions promotions = new Promotions();
    private Loyalty loyalty = new Loyalty();
    private Payments payments = new Payments();
    private Inventory inventory = new Inventory();

    // Getters and Setters
    public Promotions getPromotions() { return promotions; }
    public void setPromotions(Promotions promotions) { this.promotions = promotions; }

    public Loyalty getLoyalty() { return loyalty; }
    public void setLoyalty(Loyalty loyalty) { this.loyalty = loyalty; }

    public Payments getPayments() { return payments; }
    public void setPayments(Payments payments) { this.payments = payments; }

    public Inventory getInventory() { return inventory; }
    public void setInventory(Inventory inventory) { this.inventory = inventory; }

    /**
     * Discount tier configuration.
     */
    public static class Promotions {
        private DiscountTier tier1 = new DiscountTier();
        private DiscountTier tier2 = new DiscountTier();
        private DiscountTier tier3 = new DiscountTier();

        public DiscountTier getTier1() { return tier1; }
        public void setTier1(DiscountTier tier1) { this.tier1 = tier1; }

        public DiscountTier getTier2() { return tier2; }
        public void setTier2(DiscountTier tier2) { this.tier2 = tier2; }

        public DiscountTier getTier3() { return tier3; }
        public void setTier3(DiscountTier tier3) { this.tier3 = tier3; }
    }

    /**
     * Individual discount tier.
     */
    public static class DiscountTier {
        private BigDecimal threshold = BigDecimal.ZERO;
        private BigDecimal discount = BigDecimal.ZERO;

        public BigDecimal getThreshold() { return threshold; }
        public void setThreshold(BigDecimal threshold) { this.threshold = threshold; }

        public BigDecimal getDiscount() { return discount; }
        public void setDiscount(BigDecimal discount) { this.discount = discount; }
    }

    /**
     * Loyalty points configuration.
     */
    public static class Loyalty {
        private double pointsPerDollar = 1.0;
        private int maxPoints = 500;

        public double getPointsPerDollar() { return pointsPerDollar; }
        public void setPointsPerDollar(double pointsPerDollar) { this.pointsPerDollar = pointsPerDollar; }

        public int getMaxPoints() { return maxPoints; }
        public void setMaxPoints(int maxPoints) { this.maxPoints = maxPoints; }
    }

    /**
     * Payment service configuration.
     */
    public static class Payments {
        private String authUrl;
        private int timeoutSeconds = 10;

        public String getAuthUrl() { return authUrl; }
        public void setAuthUrl(String authUrl) { this.authUrl = authUrl; }

        public int getTimeoutSeconds() { return timeoutSeconds; }
        public void setTimeoutSeconds(int timeoutSeconds) { this.timeoutSeconds = timeoutSeconds; }
    }

    /**
     * Inventory management configuration.
     */
    public static class Inventory {
        private int defaultRestockQuantity = 100;

        public int getDefaultRestockQuantity() { return defaultRestockQuantity; }
        public void setDefaultRestockQuantity(int defaultRestockQuantity) { 
            this.defaultRestockQuantity = defaultRestockQuantity; 
        }
    }
}