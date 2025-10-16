# FastAPI Order Management - Rewrite of Java Spring Boot Implementation

This is a FastAPI implementation of the Order Management feature from the Java LegacyShop application, created as part of MCP-1 ticket implementation.

## Purpose

This project demonstrates behavioral equivalence between Java Spring Boot and Python FastAPI implementations for enterprise patterns including:
- Idempotency via request headers
- Payment authorization with retry logic
- Compensating transactions (Saga pattern)
- Atomic database operations
- RFC-7807 Problem Details error format
- Comprehensive audit logging

## Specifications Source

All specifications and behavior were validated against CoreStory project #75 (Java LegacyShop) to ensure 100% behavioral compatibility.

## API Endpoints

1. **POST /api/orders** - Create order with idempotency-key header support
2. **GET /api/orders/{id}** - Retrieve order by ID
3. **GET /api/orders/customer/{email}** - Get customer orders (paginated)
4. **POST /api/orders/{id}/authorize-payment** - Authorize payment with retry logic
5. **POST /api/orders/{id}/cancel** - Cancel order with compensation

## Business Rules

### Discount Tiers
- Tier 1: 5% for subtotal $50-$99.99
- Tier 2: 10% for subtotal $100-$199.99
- Tier 3: 15% for subtotal ≥ $200
- No discount for subtotal < $50

### Validation Rules
- Customer email: required, valid format
- Order items: minimum 1 item, valid SKU, quantity ≥ 1
- Stock availability: must have sufficient stock
- Product status: only active products
- Order total: ≥ $0.01 after discounts

### Payment Retry Logic
- Max attempts: 2 retries
- Retry delay: 1 second
- Only retry on 5xx errors (transient failures)
- No retry on 4xx errors (client errors)

### Compensation Transactions
When canceling an order:
1. Validate order can be cancelled (PENDING or PAID status)
2. Restore stock levels atomically
3. Void payment if authorized
4. Update order status to CANCELLED
5. Log all compensation steps

## Enterprise Patterns

### Idempotency
- Unique `Idempotency-Key` header prevents duplicate order creation
- Keys stored in database with order reference
- Concurrent request handling with race condition prevention

### Atomic Transactions
- Stock decrement is atomic and indivisible
- Rollback on any failure in order creation process
- Prevents overselling and data inconsistencies

### Retry Logic
- Automatic retry for payment service 5xx errors
- Configurable max attempts and delay
- Exponential backoff optional

### RFC-7807 Error Format
All errors follow RFC-7807 Problem Details format:
```json
{
  "type": "/errors/validation-error",
  "title": "Invalid Request",
  "status": 400,
  "detail": "The customer email is invalid.",
  "instance": "/api/orders"
}
```

### Audit Logging
- All operations logged: order creation, cancellation, payment authorization
- Immutable audit trail
- Filterable by operation type, entity, timestamp
- Paginated for large datasets

## Database Schema

### Orders
- order_id (UUID, PK)
- customer_email (VARCHAR)
- status (VARCHAR): PENDING, PAID, SHIPPED, CANCELLED
- subtotal (DECIMAL)
- discount_amount (DECIMAL)
- total (DECIMAL)
- idempotency_key (VARCHAR, unique)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### Order Items
- item_id (UUID, PK)
- order_id (UUID, FK)
- product_sku (VARCHAR)
- product_name (VARCHAR)
- quantity (INTEGER)
- unit_price (DECIMAL)
- subtotal (DECIMAL)

### Payments
- payment_id (UUID, PK)
- order_id (UUID, FK)
- payment_status (VARCHAR): AUTHORIZED, FAILED, REFUNDED
- payment_method (VARCHAR)
- amount (DECIMAL)
- authorization_id (VARCHAR)
- retry_attempts (INTEGER)
- created_at (TIMESTAMP)

### Customers
- customer_email (VARCHAR, PK)
- name (VARCHAR)
- phone (VARCHAR)
- created_at (TIMESTAMP)

### Idempotency Records
- idempotency_key (VARCHAR, PK)
- order_id (UUID, FK)
- created_at (TIMESTAMP)
- expires_at (TIMESTAMP)

### Audit Logs
- log_id (UUID, PK)
- operation (VARCHAR)
- entity_type (VARCHAR)
- entity_id (UUID)
- details (TEXT/JSON)
- timestamp (TIMESTAMP)

## Testing

The test suite in `tests/test_order_management.py` contains 40+ integration tests covering:
- All 5 API endpoints
- Happy paths and error scenarios
- All discount tiers
- Idempotency enforcement
- Payment retry logic
- Compensation transactions
- RFC-7807 error format
- Pagination and sorting
- Edge cases

## Technology Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- Pydantic for validation
- httpx for async HTTP client
- pytest for testing
- In-memory SQLite database for POC

## Implementation Status

This is a proof-of-concept implementation demonstrating:
1. Complete API endpoint implementation matching Java version
2. All enterprise patterns preserved
3. Comprehensive test suite validating behavioral equivalence
4. Documentation of migration patterns

## CoreStory Usage

This implementation was guided by 7 CoreStory queries to project #75:
1. Project verification and ingestion status check
2. Created conversation for Order Management analysis
3. Queried POST /api/orders workflow details
4. Queried other endpoint specifications and error formats
5. Retrieved complete technical specification
6. Queried database schema and implementation details

See `corestory_usage_log.md` in the root directory for complete CoreStory interaction log.

## Future Enhancements

For production use, consider:
- PostgreSQL instead of SQLite
- Proper secrets management
- Distributed transaction coordination
- Performance optimization
- Additional security measures
- Comprehensive monitoring and alerting
