package com.example.legacyshop.service;

import com.example.legacyshop.config.BusinessConfig;
import com.example.legacyshop.entity.AuditLog;
import com.example.legacyshop.entity.Customer;
import com.example.legacyshop.entity.IdempotencyRecord;
import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.repository.AuditLogRepository;
import com.example.legacyshop.repository.CustomerRepository;
import com.example.legacyshop.repository.IdempotencyRecordRepository;
import com.example.legacyshop.repository.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Service for loyalty points accrual with idempotency and caps.
 * 
 * Key patterns:
 * - Idempotent points accrual (process each order only once)
 * - Business cap enforcement (max 500 points)
 * - Scheduled processing of PAID orders
 * - Config-driven points calculation
 */
@Service
public class LoyaltyService {

    private static final Logger logger = LoggerFactory.getLogger(LoyaltyService.class);

    private final OrderRepository orderRepository;
    private final CustomerRepository customerRepository;
    private final AuditLogRepository auditLogRepository;
    private final IdempotencyRecordRepository idempotencyRecordRepository;
    private final BusinessConfig businessConfig;

    public LoyaltyService(OrderRepository orderRepository,
                         CustomerRepository customerRepository,
                         AuditLogRepository auditLogRepository,
                         IdempotencyRecordRepository idempotencyRecordRepository,
                         BusinessConfig businessConfig) {
        this.orderRepository = orderRepository;
        this.customerRepository = customerRepository;
        this.auditLogRepository = auditLogRepository;
        this.idempotencyRecordRepository = idempotencyRecordRepository;
        this.businessConfig = businessConfig;
    }

    /**
     * Scheduled loyalty points processing.
     * Runs every 30 minutes to process newly PAID orders.
     * 
     * Cron expression: "0 star-slash-30 * * * ?" = Every 30 minutes
     */
    @Scheduled(cron = "0 */30 * * * ?")
    @Transactional
    public void processLoyaltyPoints() {
        logger.info("Starting loyalty points processing");
        
        try {
            // Look for orders that became PAID in the last hour
            LocalDateTime since = LocalDateTime.now().minusHours(1);
            int totalProcessed = 0;
            
            // Process in batches
            Pageable pageable = PageRequest.of(0, 50);
            Page<OrderEntity> ordersPage;
            
            do {
                ordersPage = orderRepository.findPaidOrdersSince(since, pageable);
                
                for (OrderEntity order : ordersPage.getContent()) {
                    if (processOrderForLoyaltyPoints(order)) {
                        totalProcessed++;
                    }
                }
                
                pageable = ordersPage.nextPageable();
                
            } while (ordersPage.hasNext());
            
            logger.info("Loyalty points processing completed. Processed {} orders", totalProcessed);
            
        } catch (Exception e) {
            logger.error("Error during loyalty points processing", e);
        }
    }

    /**
     * Process a single order for loyalty points with idempotency.
     */
    @Transactional
    public boolean processOrderForLoyaltyPoints(OrderEntity order) {
        String idempotencyKey = "LOYALTY_" + order.getId();
        
        // Check if we've already processed this order for loyalty points
        if (idempotencyRecordRepository.existsByIdempotencyKey(idempotencyKey)) {
            logger.debug("Order {} already processed for loyalty points", order.getId());
            return false;
        }

        // Only process PAID orders
        if (order.getStatus() != OrderEntity.OrderStatus.PAID) {
            return false;
        }

        try {
            // Calculate points based on order total
            int pointsToAdd = calculateLoyaltyPoints(order.getTotal());
            
            if (pointsToAdd > 0) {
                Customer customer = order.getCustomer();
                int previousPoints = customer.getLoyaltyPoints();
                
                // Apply business cap
                customer.addLoyaltyPoints(pointsToAdd, businessConfig.getLoyalty().getMaxPoints());
                customerRepository.save(customer);
                
                int actualPointsAdded = customer.getLoyaltyPoints() - previousPoints;
                
                // Create idempotency record
                IdempotencyRecord record = new IdempotencyRecord(idempotencyKey, "LOYALTY_POINTS");
                record.setResult(customer.getId(), String.valueOf(actualPointsAdded));
                idempotencyRecordRepository.save(record);
                
                // Create audit log
                AuditLog auditLog = AuditLog.loyaltyPointsLog(customer.getId(), actualPointsAdded);
                auditLog.setDetails(
                    String.format("Added %d loyalty points for order %d. Customer %s now has %d points (capped at %d)",
                                 actualPointsAdded, order.getId(), customer.getEmail(), 
                                 customer.getLoyaltyPoints(), businessConfig.getLoyalty().getMaxPoints())
                );
                auditLogRepository.save(auditLog);
                
                logger.debug("Added {} loyalty points to customer {} for order {}", 
                           actualPointsAdded, customer.getEmail(), order.getId());
                
                return true;
            }
            
        } catch (Exception e) {
            logger.error("Error processing loyalty points for order {}", order.getId(), e);
        }
        
        return false;
    }

    /**
     * Calculate loyalty points based on order total.
     */
    private int calculateLoyaltyPoints(BigDecimal orderTotal) {
        if (orderTotal == null) {
            return 0;
        }
        
        double pointsPerDollar = businessConfig.getLoyalty().getPointsPerDollar();
        double totalPoints = orderTotal.doubleValue() * pointsPerDollar;
        
        // Round down to whole points
        return (int) Math.floor(totalPoints);
    }

    /**
     * Manual trigger for loyalty points processing (useful for testing).
     */
    @Transactional
    public int triggerManualLoyaltyProcessing() {
        logger.info("Manual loyalty points processing triggered");
        
        // Process all PAID orders from the last 24 hours
        LocalDateTime since = LocalDateTime.now().minusHours(24);
        int totalProcessed = 0;
        
        Pageable pageable = PageRequest.of(0, 100);
        Page<OrderEntity> ordersPage;
        
        do {
            ordersPage = orderRepository.findPaidOrdersSince(since, pageable);
            
            for (OrderEntity order : ordersPage.getContent()) {
                if (processOrderForLoyaltyPoints(order)) {
                    totalProcessed++;
                }
            }
            
            pageable = ordersPage.nextPageable();
            
        } while (ordersPage.hasNext());
        
        logger.info("Manual loyalty points processing completed. Processed {} orders", totalProcessed);
        return totalProcessed;
    }

    /**
     * Get customer's current loyalty points.
     */
    @Transactional(readOnly = true)
    public int getCustomerLoyaltyPoints(String email) {
        return customerRepository.findByEmail(email)
            .map(Customer::getLoyaltyPoints)
            .orElse(0);
    }
}