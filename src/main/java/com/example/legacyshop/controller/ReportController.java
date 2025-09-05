package com.example.legacyshop.controller;

import com.example.legacyshop.dto.OrderReportResponse;
import com.example.legacyshop.service.ReportService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

/**
 * REST controller for reporting endpoints with pagination.
 * 
 * Key patterns:
 * - Date range parameters with proper formatting
 * - Pagination with sensible defaults
 * - Multiple report types (convenience methods)
 * - N+1 prevention through service layer
 */
@RestController
@RequestMapping("/api/reports")
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    /**
     * Get order report with custom date range.
     * GET /api/reports/orders?startDate=2023-01-01T00:00:00&endDate=2023-01-31T23:59:59&page=0&size=50
     */
    @GetMapping("/orders")
    public ResponseEntity<Page<OrderReportResponse>> getOrderReport(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @PageableDefault(size = 50, sort = "createdAt") Pageable pageable) {
        
        Page<OrderReportResponse> report = reportService.getOrderReport(startDate, endDate, pageable);
        return ResponseEntity.ok(report);
    }

    /**
     * Get today's orders report.
     * GET /api/reports/orders/today?page=0&size=50
     */
    @GetMapping("/orders/today")
    public ResponseEntity<Page<OrderReportResponse>> getTodaysReport(
            @PageableDefault(size = 50, sort = "createdAt") Pageable pageable) {
        
        Page<OrderReportResponse> report = reportService.getTodaysReport(pageable);
        return ResponseEntity.ok(report);
    }

    /**
     * Get last 30 days orders report.
     * GET /api/reports/orders/last-30-days?page=0&size=50
     */
    @GetMapping("/orders/last-30-days")
    public ResponseEntity<Page<OrderReportResponse>> getLast30DaysReport(
            @PageableDefault(size = 50, sort = "createdAt") Pageable pageable) {
        
        Page<OrderReportResponse> report = reportService.getLast30DaysReport(pageable);
        return ResponseEntity.ok(report);
    }

    /**
     * Get current month orders report.
     * GET /api/reports/orders/current-month?page=0&size=50
     */
    @GetMapping("/orders/current-month")
    public ResponseEntity<Page<OrderReportResponse>> getCurrentMonthReport(
            @PageableDefault(size = 50, sort = "createdAt") Pageable pageable) {
        
        Page<OrderReportResponse> report = reportService.getCurrentMonthReport(pageable);
        return ResponseEntity.ok(report);
    }
}