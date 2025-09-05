#!/bin/bash

# LegacyShop API Testing with curl
# Make sure the application is running on localhost:8080

BASE_URL="http://localhost:8080"

echo "=== LegacyShop API Testing Script ==="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Create a new product
echo "1. Creating a new product..."
curl -s -X POST "$BASE_URL/api/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "CURL-TEST-001",
    "name": "Curl Test Product",
    "description": "Product created via curl script",
    "price": 149.99,
    "stockQuantity": 25
  }' | python3 -m json.tool

echo -e "\n"

# Test 2: Get all products (paginated)
echo "2. Getting all products..."
curl -s "$BASE_URL/api/products?page=0&size=5&sort=name,asc" | python3 -m json.tool

echo -e "\n"

# Test 3: Create an order with idempotency key
echo "3. Creating an order with idempotency key..."
IDEMPOTENCY_KEY="curl-test-$(date +%s)"
curl -s -X POST "$BASE_URL/api/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "customerEmail": "curl-test@example.com",
    "items": [
      {
        "productSku": "LAPTOP-001",
        "quantity": 1
      },
      {
        "productSku": "MOUSE-001", 
        "quantity": 2
      }
    ]
  }' | python3 -m json.tool

echo -e "\n"

# Test 4: Test idempotency - same key should return same result
echo "4. Testing idempotency (same key)..."
curl -s -X POST "$BASE_URL/api/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "customerEmail": "curl-test@example.com",
    "items": [
      {
        "productSku": "LAPTOP-001",
        "quantity": 1
      }
    ]
  }' | python3 -m json.tool

echo -e "\n"

# Test 5: Get customer orders
echo "5. Getting customer orders..."
curl -s "$BASE_URL/api/orders/customer/john.doe@example.com?page=0&size=3" | python3 -m json.tool

echo -e "\n"

# Test 6: Get today's report
echo "6. Getting today's orders report..."
curl -s "$BASE_URL/api/reports/orders/today?page=0&size=10" | python3 -m json.tool

echo -e "\n"

# Test 7: Test error handling - duplicate SKU
echo "7. Testing error handling (duplicate SKU)..."
curl -s -X POST "$BASE_URL/api/products" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "Duplicate SKU Test",
    "description": "This should fail with 409",
    "price": 99.99,
    "stockQuantity": 10
  }' | python3 -m json.tool

echo -e "\n"

# Test 8: Test validation error
echo "8. Testing validation error..."
curl -s -X POST "$BASE_URL/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customerEmail": "invalid-email",
    "items": [
      {
        "productSku": "",
        "quantity": -1
      }
    ]
  }' | python3 -m json.tool

echo -e "\n"

# Test 9: Test insufficient stock
echo "9. Testing insufficient stock..."
curl -s -X POST "$BASE_URL/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customerEmail": "stocktest@example.com",
    "items": [
      {
        "productSku": "LAPTOP-001",
        "quantity": 1000
      }
    ]
  }' | python3 -m json.tool

echo -e "\n"

# Test 10: Trigger admin operations
echo "10. Triggering loyalty points processing..."
curl -s -X POST "$BASE_URL/api/admin/trigger-loyalty-processing" | python3 -m json.tool

echo -e "\n"

# Test 11: Mock payment service
echo "11. Testing mock payment service..."
curl -s -X POST "$BASE_URL/mock/payment/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "99.99",
    "currency": "USD",
    "paymentMethod": "CARD"
  }' | python3 -m json.tool

echo -e "\n"

# Test 12: Search products
echo "12. Searching products..."
curl -s "$BASE_URL/api/products/search?name=laptop&page=0&size=3" | python3 -m json.tool

echo -e "\n"

echo "=== Testing Complete ==="
echo ""
echo "Key URLs for further testing:"
echo "- H2 Console: $BASE_URL/h2-console"
echo "- API Base: $BASE_URL/api"
echo "- Mock Payment: $BASE_URL/mock/payment"
echo ""
echo "Sample customer emails in seed data:"
echo "- john.doe@example.com"
echo "- jane.smith@example.com" 
echo "- sarah.wilson@example.com (near loyalty cap)"
echo "- olivia.anderson@example.com (at loyalty cap)"