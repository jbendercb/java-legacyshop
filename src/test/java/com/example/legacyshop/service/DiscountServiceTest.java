package com.example.legacyshop.service;

import com.example.legacyshop.config.BusinessConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.when;

/**
 * Unit tests for DiscountService focusing on discount tier calculations.
 * 
 * Tests cover:
 * - Discount tier thresholds from configuration
 * - Correct discount percentage application
 * - Edge cases (null values, zero amounts)
 */
@ExtendWith(MockitoExtension.class)
class DiscountServiceTest {

    @Mock
    private BusinessConfig businessConfig;

    @Mock
    private BusinessConfig.Promotions promotions;

    @Mock
    private BusinessConfig.DiscountTier tier1;

    @Mock
    private BusinessConfig.DiscountTier tier2;

    @Mock
    private BusinessConfig.DiscountTier tier3;

    @InjectMocks
    private DiscountService discountService;

    @BeforeEach
    void setUp() {
        // Setup configuration mocks to match application.yaml (using lenient for unused stubs)
        lenient().when(businessConfig.getPromotions()).thenReturn(promotions);
        lenient().when(promotions.getTier1()).thenReturn(tier1);
        lenient().when(promotions.getTier2()).thenReturn(tier2);
        lenient().when(promotions.getTier3()).thenReturn(tier3);

        // Tier 1: $50+ -> 5% discount
        lenient().when(tier1.getThreshold()).thenReturn(new BigDecimal("50.00"));
        lenient().when(tier1.getDiscount()).thenReturn(new BigDecimal("0.05"));

        // Tier 2: $100+ -> 10% discount
        lenient().when(tier2.getThreshold()).thenReturn(new BigDecimal("100.00"));
        lenient().when(tier2.getDiscount()).thenReturn(new BigDecimal("0.10"));

        // Tier 3: $200+ -> 15% discount
        lenient().when(tier3.getThreshold()).thenReturn(new BigDecimal("200.00"));
        lenient().when(tier3.getDiscount()).thenReturn(new BigDecimal("0.15"));
    }

    @Test
    void calculateDiscount_NoDiscount_AmountBelowThreshold() {
        // Given
        BigDecimal subtotal = new BigDecimal("25.00");

        // When
        BigDecimal discount = discountService.calculateDiscount(subtotal);

        // Then
        assertEquals(new BigDecimal("0.00"), discount);
    }

    @Test
    void calculateDiscount_Tier1_5PercentDiscount() {
        // Given
        BigDecimal subtotal = new BigDecimal("75.00");

        // When
        BigDecimal discount = discountService.calculateDiscount(subtotal);

        // Then
        assertEquals(new BigDecimal("3.75"), discount); // 75 * 0.05 = 3.75
    }

    @Test
    void calculateDiscount_Tier2_10PercentDiscount() {
        // Given
        BigDecimal subtotal = new BigDecimal("150.00");

        // When
        BigDecimal discount = discountService.calculateDiscount(subtotal);

        // Then
        assertEquals(new BigDecimal("15.00"), discount); // 150 * 0.10 = 15.00
    }

    @Test
    void calculateDiscount_Tier3_15PercentDiscount() {
        // Given
        BigDecimal subtotal = new BigDecimal("300.00");

        // When
        BigDecimal discount = discountService.calculateDiscount(subtotal);

        // Then
        assertEquals(new BigDecimal("45.00"), discount); // 300 * 0.15 = 45.00
    }

    @Test
    void calculateDiscount_ExactThreshold_AppliesDiscount() {
        // Given - exactly at tier 2 threshold
        BigDecimal subtotal = new BigDecimal("100.00");

        // When
        BigDecimal discount = discountService.calculateDiscount(subtotal);

        // Then
        assertEquals(new BigDecimal("10.00"), discount); // 100 * 0.10 = 10.00
    }

    @Test
    void calculateDiscount_NullSubtotal_ReturnsZero() {
        // Given
        BigDecimal subtotal = null;

        // When
        BigDecimal discount = discountService.calculateDiscount(subtotal);

        // Then
        assertEquals(new BigDecimal("0.00"), discount);
    }

    @Test
    void getDiscountRate_ReturnsCorrectRate() {
        // Test each tier's rate
        assertEquals(new BigDecimal("0.05"), discountService.getDiscountRate(new BigDecimal("75.00")));
        assertEquals(new BigDecimal("0.10"), discountService.getDiscountRate(new BigDecimal("150.00")));
        assertEquals(new BigDecimal("0.15"), discountService.getDiscountRate(new BigDecimal("300.00")));
        assertEquals(new BigDecimal("0.00"), discountService.getDiscountRate(new BigDecimal("25.00")));
    }
}