#!/bin/bash


BASE_URL="http://localhost:8000/api"

echo "=== FastAPI LegacyShop API Tests ==="
echo

echo "1. Getting all products..."
curl -s "$BASE_URL/products/" | jq '.' || echo "Failed to get products"
echo

echo "2. Creating a new product..."
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Widget",
    "sku": "TEST-001",
    "price": 29.99,
    "stock_quantity": 100,
    "description": "A test product for API demonstration"
  }')
echo "$PRODUCT_RESPONSE" | jq '.' || echo "Failed to create product"
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | jq -r '.id' 2>/dev/null)
echo

echo "3. Creating an order (first attempt)..."
IDEMPOTENCY_KEY="test-$(date +%s)"
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "customer_email": "test@example.com",
    "items": [{"product_id": 1, "quantity": 2}]
  }')
echo "$ORDER_RESPONSE" | jq '.' || echo "Failed to create order"
ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.id' 2>/dev/null)
echo

echo "4. Creating the same order again (testing idempotency)..."
curl -s -X POST "$BASE_URL/orders/" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "customer_email": "test@example.com",
    "items": [{"product_id": 1, "quantity": 2}]
  }' | jq '.' || echo "Failed idempotency test"
echo

if [ "$ORDER_ID" != "null" ] && [ -n "$ORDER_ID" ]; then
  echo "5. Getting order details for order $ORDER_ID..."
  curl -s "$BASE_URL/orders/$ORDER_ID" | jq '.' || echo "Failed to get order"
  echo
fi

echo "6. Getting customer orders..."
curl -s "$BASE_URL/orders/customer/test@example.com" | jq '.' || echo "Failed to get customer orders"
echo

echo "7. Testing payment authorization..."
curl -s -X POST "http://localhost:8000/mock/payment/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 59.98,
    "order_id": 1,
    "card_number": "4111111111111111",
    "expiry_month": 12,
    "expiry_year": 2025,
    "cvv": "123"
  }' | jq '.' || echo "Failed payment authorization"
echo

echo "8. Getting order reports..."
curl -s "$BASE_URL/reports/orders/?page=0&size=5" | jq '.' || echo "Failed to get reports"
echo

echo "9. Triggering inventory replenishment..."
curl -s -X POST "$BASE_URL/admin/trigger-replenishment/" | jq '.' || echo "Failed to trigger replenishment"
echo

echo "10. Searching products by name..."
curl -s "$BASE_URL/products/search/name/Widget/" | jq '.' || echo "Failed to search products"
echo

echo "=== API Tests Complete ==="
echo "Check the server logs for detailed processing information."
