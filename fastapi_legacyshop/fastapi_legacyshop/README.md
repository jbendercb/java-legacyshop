# FastAPI LegacyShop

A Python FastAPI migration of the Java Spring Boot LegacyShop monolith, maintaining complete functional parity with the original implementation.

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd fastapi_legacyshop

# Install dependencies
poetry install

# Run database migrations
poetry run alembic upgrade head

# Start the server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## Architecture

This FastAPI application mirrors the Java Spring Boot architecture:

- **Models** (`app/models/`): SQLAlchemy models equivalent to JPA entities
- **Schemas** (`app/schemas/`): Pydantic models for request/response validation (DTOs)
- **Routers** (`app/routers/`): FastAPI routers equivalent to Spring controllers
- **Services** (`app/services/`): Business logic layer
- **Database** (`app/database.py`): SQLAlchemy configuration and session management
- **Config** (`app/config.py`): Application configuration with environment variable support

## Key Features

### Order Processing Pipeline
- Atomic order creation with stock validation and decrement
- Discount calculation based on configurable tiers (5%, 10%, 15%)
- Idempotency support using `Idempotency-Key` header
- Comprehensive audit logging

### Payment Processing
- External payment gateway integration with retry logic
- Automatic retry on 5xx errors (once)
- 4xx errors mapped to domain validation errors
- Payment voiding for cancelled orders

### Scheduled Jobs
- Nightly inventory replenishment (configurable schedule)
- Loyalty points processing every 30 minutes
- Manual trigger endpoints for testing

### Loyalty System
- Points calculation: `floor(order_total / 10)`
- Maximum 500 points per order
- Idempotent processing prevents duplicate points

### Reporting
- Paginated order reports with filtering
- Optimized queries to avoid N+1 problems
- Status and date range filtering

## API Endpoints

### Products
- `GET /products` - List products with pagination
- `POST /products` - Create new product
- `GET /products/{id}` - Get product by ID
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `GET /products/search/sku/{sku}` - Find by SKU
- `GET /products/search/name/{name}` - Search by name

### Orders
- `POST /orders` - Create order (supports idempotency)
- `GET /orders/{id}` - Get order details
- `GET /orders/customer/{email}` - Get customer orders
- `POST /orders/{id}/cancel` - Cancel order
- `POST /orders/{id}/authorize-payment` - Authorize payment

### Reports
- `GET /reports/orders` - Order reports with pagination and filtering

### Admin
- `POST /admin/trigger-replenishment` - Manual inventory replenishment
- `POST /admin/trigger-loyalty` - Manual loyalty processing
- `POST /admin/replenish-product/{id}` - Replenish specific product

### Mock Payment Gateway
- `POST /mock-payment/authorize` - Simulate payment authorization
- `POST /mock-payment/void` - Simulate payment void

## Configuration

Environment variables (with defaults):

```bash
# Database
DATABASE_URL=sqlite:///./legacyshop.db

# Business Rules
DISCOUNT_TIER_1_THRESHOLD=50.00
DISCOUNT_TIER_1_PERCENTAGE=5.0
DISCOUNT_TIER_2_THRESHOLD=100.00
DISCOUNT_TIER_2_PERCENTAGE=10.0
DISCOUNT_TIER_3_THRESHOLD=200.00
DISCOUNT_TIER_3_PERCENTAGE=15.0

# Loyalty
LOYALTY_POINTS_DIVISOR=10
LOYALTY_MAX_POINTS_PER_ORDER=500

# Payments
PAYMENT_AUTH_URL=http://localhost:8000/mock-payment/authorize
PAYMENT_TIMEOUT_SECONDS=30

# Inventory
INVENTORY_REPLENISHMENT_QUANTITY=100
INVENTORY_LOW_STOCK_THRESHOLD=10
```

## Testing

### Run All Tests
```bash
poetry run pytest --verbose
```

### Test Idempotency
```bash
# First request - returns 201
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{
    "customer_email": "test@example.com",
    "items": [{"product_id": 1, "quantity": 2}]
  }'

# Duplicate request - returns 200 with same response
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{
    "customer_email": "test@example.com",
    "items": [{"product_id": 1, "quantity": 2}]
  }'
```

### Test Payment Retry Logic
The payment service automatically retries on 5xx errors from the payment gateway. You can test this by configuring the mock payment service to return 502 errors.

### Test Reporting Pagination
```bash
# Get first page
curl "http://localhost:8000/reports/orders?page=0&size=10"

# Get second page
curl "http://localhost:8000/reports/orders?page=1&size=10"

# Filter by status
curl "http://localhost:8000/reports/orders?status=COMPLETED"
```

## Migration Notes

### Java to Python Mappings

| Java Component | Python Equivalent | Notes |
|---|---|---|
| `@Entity` classes | SQLAlchemy models | Same field names and constraints |
| `@RestController` | FastAPI routers | Same endpoint paths and methods |
| `@Service` classes | Service classes | Same business logic |
| DTOs | Pydantic schemas | Same validation rules |
| `@Scheduled` | APScheduler | Same cron expressions |
| `@Retryable` | Tenacity decorators | Same retry parameters |
| `BigDecimal` | `decimal.Decimal` | Precise monetary calculations |
| JPA transactions | SQLAlchemy sessions | Same atomicity guarantees |

### Key Differences
- **Error Handling**: FastAPI uses exception handlers vs Spring's `@ControllerAdvice`
- **Dependency Injection**: FastAPI's `Depends()` vs Spring's `@Autowired`
- **Configuration**: Pydantic Settings vs Spring's `@ConfigurationProperties`
- **Async Support**: Native async/await vs Spring WebFlux
- **Database Migrations**: Alembic vs Flyway/Liquibase

### Preserved Behaviors
- ✅ Same API contracts and status codes
- ✅ RFC-7807 Problem Details error format
- ✅ Idempotency with database-backed storage
- ✅ Atomic stock operations
- ✅ Payment retry logic (once on 5xx)
- ✅ Discount tier calculations
- ✅ Loyalty points rules and caps
- ✅ Scheduled job timing
- ✅ Audit logging for all operations

## Development

### Database Migrations
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Adding New Features
1. Create/update SQLAlchemy models in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add API endpoints in `app/routers/`
5. Write tests in `tests/`
6. Generate and apply database migrations

## Troubleshooting

### Common Issues
- **Import Errors**: Ensure you're in the project directory and using `poetry run`
- **Database Locked**: Stop the server and delete `legacyshop.db` to reset
- **Port Already in Use**: Change the port with `--port 8001`
- **Test Failures**: Run `poetry run alembic upgrade head` to ensure DB is current

### Logs
Application logs include:
- Order processing steps
- Payment authorization attempts
- Stock level changes
- Scheduled job execution
- Error details with stack traces

For detailed debugging, set `LOG_LEVEL=DEBUG` in your environment.
