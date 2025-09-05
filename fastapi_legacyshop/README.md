# LegacyShop FastAPI

Run:
- pip install -r requirements.txt
- make migrate
- make seed
- make run (then open http://127.0.0.1:8000/docs)

Env (.env.example):
APP_ENV=dev
DATABASE_URL=sqlite:///./legacyshop.db
PAYMENT_RANDOM_ENABLED=false
PAYMENT_FAIL_RATE_5XX=0.10
PAYMENT_FAIL_RATE_4XX=0.05
IDEMPOTENCY_TTL_DAYS=7
SCHEDULER_ENABLED=true

Make:
- make migrate: alembic upgrade head
- make seed: python -m app.db.seed
- make run: uvicorn app.main:app --reload
- make test: pytest -q

Curl examples:
- Create product:
  curl -s -X POST http://127.0.0.1:8000/api/products -H "Content-Type: application/json" -d '{"sku":"SKU-100","name":"Test","price":12.34,"stock_quantity":10,"active":true}'
- List products:
  curl -s http://127.0.0.1:8000/api/products
- Create order with idempotency:
  BODY='{"customerEmail":"alice@example.com","items":[{"productSku":"SKU-001","quantity":2}]}'
  KEY="idem-abc-123"
  curl -s -X POST http://127.0.0.1:8000/api/orders -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" -d "$BODY"
  curl -s -X POST http://127.0.0.1:8000/api/orders -H "Content-Type: application/json" -H "Idempotency-Key: $KEY" -d "$BODY"
- Authorize payment with one-shot injected 500 to prove single retry:
  curl -s -X POST "http://127.0.0.1:8000/_admin/payment/next_failure?code=500"
  curl -s -X POST http://127.0.0.1:8000/api/orders/1/authorize-payment
- Reports (pagination):
  curl -s "http://127.0.0.1:8000/api/reports?page=1&pageSize=20"

Notes:
- Reporting uses joinedload to avoid N+1 on items/products.
- Payments are deterministic by default; randomness flags are ignored unless PAYMENT_RANDOM_ENABLED=true.
