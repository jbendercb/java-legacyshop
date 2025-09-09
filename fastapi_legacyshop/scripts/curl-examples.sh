#!/usr/bin/env bash
set -euo pipefail

base="${BASE_URL:-http://127.0.0.1:8000}"

echo "Create product"
curl -s -X POST "$base/api/products" -H "Content-Type: application/json" -d '{"sku":"SKU-100","name":"Test","price":12.34,"stock_quantity":10,"active":true}'
echo

echo "List products"
curl -s "$base/api/products"
echo

echo "Create order with idempotency"
BODY='{"customerEmail":"alice@example.com","items":[{"productSku":"SKU-001","quantity":2}]}'
KEY="idem-abc-123"
curl -s -X POST "$base/api/orders" -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" -d "$BODY"
echo
curl -s -X POST "$base/api/orders" -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" -d "$BODY"
echo

echo "Authorize payment with one-shot injected 500"
curl -s -X POST "$base/_admin/payment/next_failure?code=500"
echo
curl -s -X POST "$base/api/orders/1/authorize-payment"
echo

echo "Reports page 1"
curl -s "$base/api/reports?page=1&pageSize=20"
echo
