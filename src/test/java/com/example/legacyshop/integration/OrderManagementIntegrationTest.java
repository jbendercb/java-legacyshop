package com.example.legacyshop.integration;

import com.example.legacyshop.dto.OrderCreateRequest;
import com.example.legacyshop.dto.OrderResponse;
import com.example.legacyshop.entity.Customer;
import com.example.legacyshop.entity.Product;
import com.example.legacyshop.repository.CustomerRepository;
import com.example.legacyshop.repository.OrderRepository;
import com.example.legacyshop.repository.ProductRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.List;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for Order Management feature.
 * Tests validate the complete order lifecycle including:
 * - Order creation with idempotency
 * - Stock validation and atomic decrement
 * - Payment authorization with retry
 * - Order cancellation with compensation
 * - Error handling scenarios
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
public class OrderManagementIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private OrderRepository orderRepository;

    private Product product1;
    private Product product2;

    @BeforeEach
    public void setUp() {
        orderRepository.deleteAll();
        productRepository.deleteAll();
        customerRepository.deleteAll();

        product1 = new Product();
        product1.setSku("TEST-SKU-001");
        product1.setName("Test Product 1");
        product1.setDescription("Test Description 1");
        product1.setPrice(new BigDecimal("100.00"));
        product1.setStockQuantity(50);
        product1.setActive(true);
        product1 = productRepository.save(product1);

        product2 = new Product();
        product2.setSku("TEST-SKU-002");
        product2.setName("Test Product 2");
        product2.setDescription("Test Description 2");
        product2.setPrice(new BigDecimal("200.00"));
        product2.setStockQuantity(30);
        product2.setActive(true);
        product2 = productRepository.save(product2);
    }

    @Test
    public void testCreateOrder_Success() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(
                        new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 2),
                        new OrderCreateRequest.OrderItemRequest("TEST-SKU-002", 1)
                ));

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.customerEmail").value("customer@example.com"))
                .andExpect(jsonPath("$.status").value("PENDING"))
                .andExpect(jsonPath("$.subtotal").value(400.00))
                .andExpect(jsonPath("$.total").isNumber())
                .andExpect(jsonPath("$.items").isArray())
                .andExpect(jsonPath("$.items.length()").value(2))
                .andExpect(jsonPath("$.createdAt").exists());

        Product updatedProduct1 = productRepository.findBySku("TEST-SKU-001").orElseThrow();
        Product updatedProduct2 = productRepository.findBySku("TEST-SKU-002").orElseThrow();
        
        assert updatedProduct1.getStockQuantity() == 48;
        assert updatedProduct2.getStockQuantity() == 29;
    }

    @Test
    public void testCreateOrder_WithIdempotencyKey_Success() throws Exception {
        String idempotencyKey = "unique-key-123";
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 1)));

        MvcResult result1 = mockMvc.perform(post("/api/orders")
                        .header("Idempotency-Key", idempotencyKey)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andReturn();

        String orderId1 = objectMapper.readTree(result1.getResponse().getContentAsString())
                .get("id").asText();

        MvcResult result2 = mockMvc.perform(post("/api/orders")
                        .header("Idempotency-Key", idempotencyKey)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andReturn();

        String orderId2 = objectMapper.readTree(result2.getResponse().getContentAsString())
                .get("id").asText();

        assert orderId1.equals(orderId2);

        Product updatedProduct = productRepository.findBySku("TEST-SKU-001").orElseThrow();
        assert updatedProduct.getStockQuantity() == 49;
    }

    @Test
    public void testCreateOrder_InsufficientStock_Failure() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 100)));

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Business Rule Violation"));

        Product updatedProduct = productRepository.findBySku("TEST-SKU-001").orElseThrow();
        assert updatedProduct.getStockQuantity() == 50;
    }

    @Test
    public void testCreateOrder_ProductNotFound_Failure() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("NON-EXISTENT-SKU", 1)));

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Resource Not Found"));
    }

    @Test
    public void testCreateOrder_InactiveProduct_Failure() throws Exception {
        product1.setActive(false);
        productRepository.save(product1);

        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 1)));

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Business Rule Violation"));
    }

    @Test
    public void testGetOrder_Success() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 2)));

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andReturn();

        String orderId = objectMapper.readTree(createResult.getResponse().getContentAsString())
                .get("id").asText();

        mockMvc.perform(get("/api/orders/" + orderId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(orderId))
                .andExpect(jsonPath("$.customerEmail").value("customer@example.com"))
                .andExpect(jsonPath("$.status").value("PENDING"))
                .andExpect(jsonPath("$.items.length()").value(1));
    }

    @Test
    public void testGetOrder_NotFound_Failure() throws Exception {
        mockMvc.perform(get("/api/orders/99999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Resource Not Found"));
    }

    @Test
    public void testGetCustomerOrders_Success() throws Exception {
        OrderCreateRequest request1 = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 1)));
        OrderCreateRequest request2 = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-002", 1)));

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request1)))
                .andExpect(status().isCreated());

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request2)))
                .andExpect(status().isCreated());

        mockMvc.perform(get("/api/orders/customer/customer@example.com")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content.length()").value(2))
                .andExpect(jsonPath("$.pageable").exists())
                .andExpect(jsonPath("$.totalElements").value(2));
    }

    @Test
    public void testGetCustomerOrders_NoOrders_Success() throws Exception {
        mockMvc.perform(get("/api/orders/customer/newcustomer@example.com")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isNotFound());
    }

    @Test
    public void testCancelOrder_Success() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 5)));

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andReturn();

        String orderId = objectMapper.readTree(createResult.getResponse().getContentAsString())
                .get("id").asText();

        Product afterCreate = productRepository.findBySku("TEST-SKU-001").orElseThrow();
        assert afterCreate.getStockQuantity() == 45;

        mockMvc.perform(post("/api/orders/" + orderId + "/cancel"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(orderId))
                .andExpect(jsonPath("$.status").value("CANCELLED"));

        Product afterCancel = productRepository.findBySku("TEST-SKU-001").orElseThrow();
        assert afterCancel.getStockQuantity() == 50;
    }

    @Test
    public void testCancelOrder_NotFound_Failure() throws Exception {
        mockMvc.perform(post("/api/orders/99999/cancel"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Resource Not Found"));
    }

    @Test
    public void testCancelOrder_AlreadyCancelled_Failure() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 2)));

        MvcResult createResult = mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andReturn();

        String orderId = objectMapper.readTree(createResult.getResponse().getContentAsString())
                .get("id").asText();

        mockMvc.perform(post("/api/orders/" + orderId + "/cancel"))
                .andExpect(status().isOk());

        mockMvc.perform(post("/api/orders/" + orderId + "/cancel"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Business Rule Violation"));
    }

    @Test
    public void testCreateOrder_WithDiscount_Success() throws Exception {
        OrderCreateRequest request = createOrderRequest("customer@example.com",
                Arrays.asList(
                        new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 10),
                        new OrderCreateRequest.OrderItemRequest("TEST-SKU-002", 5)
                ));

        MvcResult result = mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.subtotal").value(2000.00))
                .andExpect(jsonPath("$.discountAmount").isNumber())
                .andReturn();

        String responseBody = result.getResponse().getContentAsString();
        OrderResponse orderResponse = objectMapper.readValue(responseBody, OrderResponse.class);
        
        assert orderResponse.getDiscountAmount().compareTo(BigDecimal.ZERO) > 0;
        assert orderResponse.getTotal().compareTo(orderResponse.getSubtotal()) < 0;
    }

    @Test
    public void testCreateOrder_ValidationError_EmptyItems() throws Exception {
        OrderCreateRequest request = new OrderCreateRequest();
        request.setCustomerEmail("customer@example.com");
        request.setItems(Arrays.asList());

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void testCreateOrder_ValidationError_InvalidEmail() throws Exception {
        OrderCreateRequest request = createOrderRequest("invalid-email",
                Arrays.asList(new OrderCreateRequest.OrderItemRequest("TEST-SKU-001", 1)));

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    private OrderCreateRequest createOrderRequest(String email, List<OrderCreateRequest.OrderItemRequest> items) {
        OrderCreateRequest request = new OrderCreateRequest();
        request.setCustomerEmail(email);
        request.setItems(items);
        return request;
    }
}
