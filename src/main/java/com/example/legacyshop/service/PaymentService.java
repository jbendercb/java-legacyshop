package com.example.legacyshop.service;

import com.example.legacyshop.config.BusinessConfig;
import com.example.legacyshop.entity.OrderEntity;
import com.example.legacyshop.entity.Payment;
import com.example.legacyshop.exception.PaymentException;
import com.example.legacyshop.exception.ResourceNotFoundException;
import com.example.legacyshop.repository.OrderRepository;
import com.example.legacyshop.repository.PaymentRepository;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;

/**
 * Payment service with retry logic and external service integration.
 * 
 * Key patterns:
 * - @Retryable for automatic retry on 5xx errors
 * - WebClient for external service calls
 * - 4xx to domain error mapping
 * - Compensation actions (void payment)
 */
@Service
@Transactional(readOnly = true)
public class PaymentService {

    private final PaymentRepository paymentRepository;
    private final OrderRepository orderRepository;
    private final WebClient webClient;
    private final BusinessConfig businessConfig;

    public PaymentService(PaymentRepository paymentRepository,
                         OrderRepository orderRepository,
                         BusinessConfig businessConfig) {
        this.paymentRepository = paymentRepository;
        this.orderRepository = orderRepository;
        this.businessConfig = businessConfig;
        this.webClient = WebClient.builder()
            .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(1024 * 1024))
            .build();
    }

    /**
     * Authorize payment with retry logic on 5xx errors.
     * Maps 4xx errors to domain exceptions.
     */
    @Transactional
    @Retryable(
        retryFor = {PaymentException.class},
        maxAttempts = 2,
        backoff = @Backoff(delay = 1000)
    )
    public Payment authorizePayment(Long orderId) {
        OrderEntity order = orderRepository.findById(orderId)
            .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + orderId));

        // Create payment record
        Payment payment = new Payment(order, order.getTotal());
        Payment savedPayment = paymentRepository.save(payment);

        try {
            // Call external payment service
            String authorizationId = callExternalPaymentService(order.getTotal());
            
            // Update payment with success
            savedPayment.authorize(authorizationId);
            Payment result = paymentRepository.save(savedPayment);

            // Update order status
            order.markAsPaid();
            orderRepository.save(order);

            return result;

        } catch (WebClientResponseException e) {
            savedPayment.incrementRetryAttempts();
            
            if (e.getStatusCode().is4xxClientError()) {
                // 4xx errors are not retryable - map to domain error
                String errorMessage = "Payment authorization failed: " + e.getResponseBodyAsString();
                savedPayment.fail(errorMessage);
                paymentRepository.save(savedPayment);
                throw new PaymentException(errorMessage, false);
                
            } else if (e.getStatusCode().is5xxServerError()) {
                // 5xx errors are retryable
                String errorMessage = "Payment service temporarily unavailable";
                savedPayment.fail(errorMessage);
                paymentRepository.save(savedPayment);
                throw new PaymentException(errorMessage, true);
                
            } else {
                // Other errors
                String errorMessage = "Unexpected payment error: " + e.getStatusCode();
                savedPayment.fail(errorMessage);
                paymentRepository.save(savedPayment);
                throw new PaymentException(errorMessage, false);
            }
        } catch (Exception e) {
            // Network or other errors - treat as retryable
            savedPayment.incrementRetryAttempts();
            String errorMessage = "Payment authorization failed: " + e.getMessage();
            savedPayment.fail(errorMessage);
            paymentRepository.save(savedPayment);
            throw new PaymentException(errorMessage, true);
        }
    }

    /**
     * Void payment (compensation action for order cancellation).
     */
    @Transactional
    public void voidPayment(Long paymentId) {
        Payment payment = paymentRepository.findById(paymentId)
            .orElseThrow(() -> new ResourceNotFoundException("Payment not found with id: " + paymentId));

        if (payment.getStatus() != Payment.PaymentStatus.AUTHORIZED) {
            throw new IllegalStateException("Can only void authorized payments");
        }

        try {
            // Call external service to void payment
            callExternalVoidService(payment.getExternalAuthorizationId());
            
            // Update payment status
            payment.voidPayment();
            paymentRepository.save(payment);

        } catch (Exception e) {
            // Log error but don't fail the cancellation process
            // In production, this might queue for retry or alert operations
            throw new PaymentException("Failed to void payment: " + e.getMessage(), false);
        }
    }

    /**
     * Call external payment authorization service.
     * This demonstrates the integration point that could fail with 4xx/5xx.
     */
    private String callExternalPaymentService(BigDecimal amount) {
        try {
            Map<String, Object> request = Map.of(
                "amount", amount.toString(),
                "currency", "USD",
                "paymentMethod", "CARD"
            );

            Map<String, Object> response = webClient.post()
                .uri(businessConfig.getPayments().getAuthUrl())
                .bodyValue(request)
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(businessConfig.getPayments().getTimeoutSeconds()))
                .block();

            if (response != null && response.containsKey("authorizationId")) {
                return (String) response.get("authorizationId");
            } else {
                throw new PaymentException("Invalid response from payment service", false);
            }

        } catch (WebClientResponseException e) {
            throw e; // Re-throw to be handled by retry logic
        }
    }

    /**
     * Call external payment void service.
     */
    private void callExternalVoidService(String authorizationId) {
        Map<String, Object> request = Map.of("authorizationId", authorizationId);

        webClient.post()
            .uri(businessConfig.getPayments().getAuthUrl() + "/void")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(Void.class)
            .timeout(Duration.ofSeconds(businessConfig.getPayments().getTimeoutSeconds()))
            .block();
    }

    /**
     * Get payment by order ID.
     */
    public Payment getPaymentByOrderId(Long orderId) {
        return paymentRepository.findByOrderId(orderId)
            .orElseThrow(() -> new ResourceNotFoundException("Payment not found for order: " + orderId));
    }
}