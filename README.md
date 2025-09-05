# LegacyShop - Enterprise E-Commerce Monolith

A comprehensive Java 17 Spring Boot 3 monolith demonstrating 10 common enterprise application patterns and business flows.

## Overview

LegacyShop is a feature-complete e-commerce backend that showcases real-world enterprise patterns including:

- **Product CRUD** with validation and SKU uniqueness
- **Order placement pipeline** with atomic stock management
- **Payment authorization** with retry logic and external service integration  
- **Order cancellation** with compensating actions
- **Scheduled inventory replenishment** with audit logging
- **Loyalty points system** with idempotency and business caps
- **Config-driven promotions** and discount tiers
- **Reporting endpoints** with pagination and N+1 prevention
- **Problem-Details JSON** error handling (RFC-7807)
- **Idempotency support** via request headers

## Architecture Highlights

### Key Design Patterns
- **Atomic Transactions**: Order placement with rollback on failures
- **Idempotency**: Prevent duplicate operations via keys
- **Compensation**: Stock restoration on order cancellation  
- **Retry Logic**: Payment service integration with @Retryable
- **Config-Driven**: Business rules externalized to YAML
- **Audit Logging**: Complete business operation tracking
- **Problem Details**: RFC-7807 compliant error responses

### Technology Stack
- **Java 17** with modern language features
- **Spring Boot 3.2.0** with auto-configuration
- **Spring Data JPA** with optimized queries
- **H2 Database** with PostgreSQL compatibility mode
- **Maven Wrapper** for build reproducibility
- **JUnit 5** with comprehensive test coverage

## Quick Start

### Prerequisites
- Java 17 or higher
- No additional installations required (uses Maven Wrapper + H2)

### Running the Application

1. **Clone and navigate to the project:**
   ```bash
   cd legacy-shop
   ```

2. **Run the application:**
   ```bash
   ./mvnw spring-boot:run
   ```
   
   On Windows:
   ```cmd
   mvnw.cmd spring-boot:run
   ```

3. **Verify it's running:**
   ```bash
   curl http://localhost:8080/api/products
   ```

The application will start on `http://localhost:8080` with sample data pre-loaded.

### Database Access

- **H2 Console**: http://localhost:8080/h2-console
  - JDBC URL: `jdbc:h2:mem:legacyshop;MODE=PostgreSQL;DB_CLOSE_DELAY=-1`
  - Username: `sa`
  - Password: (leave empty)

## API Examples

### Quick Test with curl

Run the included test script:
```bash
./curl-examples.sh
```

### Core Operations

#### 1. Product Management
```bash
# Create product
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "DEMO-001",
    "name": "Demo Product", 
    "description": "Sample product",
    "price": 99.99,
    "stockQuantity": 50
  }'

# Get products (paginated)
curl "http://localhost:8080/api/products?page=0&size=5&sort=name,asc"

# Search products
curl "http://localhost:8080/api/products/search?name=laptop"
```

#### 2. Order Placement (Atomic Pipeline)
```bash
# Create order with idempotency
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: my-unique-key-123" \
  -d '{
    "customerEmail": "test@example.com",
    "items": [
      {"productSku": "LAPTOP-001", "quantity": 1},
      {"productSku": "MOUSE-001", "quantity": 2}
    ]
  }'

# Test idempotency (same key returns same result)
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: my-unique-key-123" \
  -d '{
    "customerEmail": "different@example.com",
    "items": [{"productSku": "KEYBOARD-001", "quantity": 1}]
  }'
```

#### 3. Payment Authorization with Retry
```bash
# Authorize payment (will retry on 5xx errors)
curl -X POST http://localhost:8080/api/orders/1/authorize-payment

# Test mock payment service directly
curl -X POST http://localhost:8080/mock/payment/authorize \
  -H "Content-Type: application/json" \
  -d '{"amount": "99.99", "currency": "USD", "paymentMethod": "CARD"}'
```

#### 4. Order Cancellation with Compensation
```bash
# Cancel order (restores stock, voids payment)
curl -X POST http://localhost:8080/api/orders/3/cancel
```

#### 5. Reporting with Pagination
```bash
# Today's orders
curl "http://localhost:8080/api/reports/orders/today?page=0&size=10"

# Last 30 days
curl "http://localhost:8080/api/reports/orders/last-30-days"

# Custom date range
curl "http://localhost:8080/api/reports/orders?startDate=2023-01-01T00:00:00&endDate=2023-12-31T23:59:59"
```

### Error Handling Examples

The API returns RFC-7807 Problem Details for all error scenarios:

```bash
# 409 Conflict - Duplicate SKU
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{"sku": "LAPTOP-001", "name": "Duplicate", "price": 99.99}'

# 400 Bad Request - Validation Error  
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customerEmail": "invalid-email", "items": []}'

# 400 Bad Request - Business Rule Violation
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerEmail": "test@example.com",
    "items": [{"productSku": "LAPTOP-001", "quantity": 1000}]
  }'
```

### Administrative Operations

```bash
# Trigger scheduled jobs manually
curl -X POST http://localhost:8080/api/admin/trigger-replenishment
curl -X POST http://localhost:8080/api/admin/trigger-loyalty-processing

# Replenish specific product
curl -X POST "http://localhost:8080/api/admin/replenish-product/1?quantity=100"
```

## Business Rules Demonstrated

### 1. Discount Tiers (Config-Driven)
- **Tier 1**: Orders ≥ $50 → 5% discount
- **Tier 2**: Orders ≥ $100 → 10% discount  
- **Tier 3**: Orders ≥ $200 → 15% discount

### 2. Loyalty Points System
- **Accrual**: 1 point per dollar spent (configurable)
- **Cap**: Maximum 500 points per customer
- **Idempotency**: Orders processed only once
- **Trigger**: Only PAID orders earn points

### 3. Inventory Management
- **Atomic Stock Decrement**: Order creation decrements stock atomically
- **Stock Validation**: Orders fail if insufficient inventory
- **Compensation**: Cancelled orders restore stock
- **Scheduled Replenishment**: Nightly job restocks low inventory

### 4. Payment Processing
- **Retry Logic**: Automatic retry on 5xx errors (max 2 attempts)
- **Error Mapping**: 4xx errors mapped to domain exceptions
- **Compensation**: Payments voided on order cancellation
- **External Integration**: WebClient-based service calls

## Testing

### Running Tests
```bash
# Unit tests
./mvnw test

# Integration tests  
./mvnw test -Dtest="*IntegrationTest"

# All tests with coverage
./mvnw clean test
```

### Test Coverage
The test suite covers critical business rules:
- ✅ SKU uniqueness validation
- ✅ Discount tier calculations  
- ✅ Atomic order placement with rollback
- ✅ Stock validation and compensation
- ✅ Idempotency behavior
- ✅ Loyalty points caps and duplicate prevention
- ✅ Payment retry logic

### Sample Test Data
The application starts with pre-loaded test data including:
- **15 Products** (laptops, peripherals, accessories)
- **10 Customers** with varying loyalty points
- **10 Orders** in different statuses (PENDING, PAID, SHIPPED, CANCELLED)
- **Sample Payments** and audit logs

## Project Structure

```
src/main/java/com/example/legacyshop/
├── LegacyShopApplication.java          # Main Spring Boot application
├── config/
│   └── BusinessConfig.java            # Config-driven business rules  
├── controller/                         # REST endpoints
│   ├── ProductController.java         # Product CRUD operations
│   ├── OrderController.java           # Order management + idempotency
│   ├── ReportController.java          # Paginated reporting
│   ├── AdminController.java           # Administrative operations
│   └── MockPaymentController.java     # Mock external service
├── service/                            # Business logic layer
│   ├── ProductService.java            # Product operations + validation
│   ├── OrderService.java              # Atomic order pipeline
│   ├── PaymentService.java            # External service + retry
│   ├── CustomerService.java           # Customer management
│   ├── DiscountService.java           # Config-driven discounts
│   ├── LoyaltyService.java            # Points accrual + caps
│   ├── InventoryService.java          # Scheduled replenishment
│   └── ReportService.java             # N+1 prevention
├── entity/                             # JPA entities with business logic
├── repository/                         # Data access with custom queries  
├── dto/                               # Request/response objects
└── exception/                         # Custom exceptions + handler

src/main/resources/
├── application.yaml                    # Main configuration
├── schema.sql                         # Database schema
└── data.sql                           # Seed data

src/test/                              # Comprehensive test suite
├── java/.../service/                  # Unit tests for business logic
└── java/.../integration/             # End-to-end integration tests
```

## Configuration

Key configuration in `application.yaml`:

```yaml
business:
  promotions:
    tier1: {threshold: 50.00, discount: 0.05}    # 5% off $50+
    tier2: {threshold: 100.00, discount: 0.10}   # 10% off $100+  
    tier3: {threshold: 200.00, discount: 0.15}   # 15% off $200+
  loyalty:
    points-per-dollar: 1.0                       # Points earning rate
    max-points: 500                              # Business cap
  payments:
    auth-url: "http://localhost:8080/mock/payment/authorize"
    timeout-seconds: 10
  inventory:
    default-restock-quantity: 100               # Scheduled replenishment
```

## Scheduled Jobs

The application runs background jobs:

- **Loyalty Processing**: Every 30 minutes
  ```
  @Scheduled(cron = "0 */30 * * * ?")
  ```

- **Inventory Replenishment**: Nightly at 2 AM  
  ```  
  @Scheduled(cron = "0 0 2 * * ?")
  ```

Both can be triggered manually via admin endpoints for testing.

## Postman Collection

Import `LegacyShop-API.postman_collection.json` for a complete API test suite including:
- ✅ All CRUD operations
- ✅ Error scenarios with Problem Details
- ✅ Idempotency testing
- ✅ Business rule validation
- ✅ Administrative operations

## Extending the Application

### Adding New Business Rules
1. Add configuration properties to `BusinessConfig.java`
2. Update `application.yaml` with new thresholds/values
3. Implement business logic in appropriate service
4. Add comprehensive unit tests

### Adding New Entities
1. Create JPA entity with validation annotations
2. Create repository with custom queries
3. Create service layer with business logic
4. Create controller with proper error handling
5. Add audit logging where appropriate

### Integration with External Services
- Follow the `PaymentService` pattern for WebClient integration
- Use `@Retryable` for transient failure handling
- Map external errors to domain exceptions
- Add circuit breaker patterns for resilience

## Troubleshooting

### Common Issues

**Application won't start:**
- Verify Java 17+ is installed: `java -version`
- Check port 8080 is available: `lsof -i :8080`

**Tests failing:**
- Run `./mvnw clean test` for fresh build
- Check test database configuration in `application-test.yaml`

**Database issues:**
- H2 console: http://localhost:8080/h2-console
- Verify connection URL matches configuration
- Check `schema.sql` and `data.sql` for syntax errors

**API returning 500 errors:**
- Check application logs for stack traces
- Verify request payloads match DTO validation rules
- Test individual business rules in isolation

### Performance Tuning

For production deployment consider:
- Replace H2 with PostgreSQL/MySQL
- Add connection pooling configuration
- Enable JPA query caching  
- Add Redis for session/cache storage
- Configure logging levels appropriately

## License

This project is for educational and demonstration purposes. Use the patterns and code as reference for building enterprise applications.

---

**Built with Spring Boot 3 and Java 17 • Demonstrates 10+ Enterprise Patterns • Production-Ready Architecture**