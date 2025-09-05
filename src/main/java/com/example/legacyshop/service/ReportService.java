package com.example.legacyshop.service;

import com.example.legacyshop.dto.OrderReportResponse;
import com.example.legacyshop.repository.OrderRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * Service for generating reports with pagination and N+1 prevention.
 * 
 * Key patterns:
 * - JOIN FETCH queries to prevent N+1 problems
 * - Pagination for large result sets
 * - Date range filtering for time-based reports
 * - Optimized DTOs for reporting
 */
@Service
@Transactional(readOnly = true)
public class ReportService {

    private final OrderRepository orderRepository;

    public ReportService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    /**
     * Generate order report with date range filtering.
     * Uses JOIN FETCH to prevent N+1 queries.
     * 
     * Example usage:
     * - Daily reports: startDate = today 00:00, endDate = today 23:59
     * - Monthly reports: startDate = first of month, endDate = last of month
     * - Custom range: any start/end date combination
     */
    public Page<OrderReportResponse> getOrderReport(LocalDateTime startDate, 
                                                   LocalDateTime endDate, 
                                                   Pageable pageable) {
        // The repository query uses JOIN FETCH to eagerly load:
        // - Customer data (prevents N+1 when accessing customer info)
        // - Order items (prevents N+1 when counting items)
        // - Payment data (included in entity fetch)
        
        return orderRepository.findOrdersForReport(startDate, endDate, pageable)
            .map(OrderReportResponse::from);
    }

    /**
     * Get order report for the last 30 days.
     * Convenience method for common reporting need.
     */
    public Page<OrderReportResponse> getLast30DaysReport(Pageable pageable) {
        LocalDateTime endDate = LocalDateTime.now();
        LocalDateTime startDate = endDate.minusDays(30);
        
        return getOrderReport(startDate, endDate, pageable);
    }

    /**
     * Get order report for today.
     * Useful for daily operational reports.
     */
    public Page<OrderReportResponse> getTodaysReport(Pageable pageable) {
        LocalDateTime startOfDay = LocalDateTime.now().toLocalDate().atStartOfDay();
        LocalDateTime endOfDay = startOfDay.plusDays(1).minusNanos(1);
        
        return getOrderReport(startOfDay, endOfDay, pageable);
    }

    /**
     * Get order report for current month.
     * Useful for monthly business reviews.
     */
    public Page<OrderReportResponse> getCurrentMonthReport(Pageable pageable) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfMonth = now.toLocalDate().withDayOfMonth(1).atStartOfDay();
        LocalDateTime endOfMonth = startOfMonth.plusMonths(1).minusNanos(1);
        
        return getOrderReport(startOfMonth, endOfMonth, pageable);
    }
}