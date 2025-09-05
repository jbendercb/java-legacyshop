# LegacyShop Java -> FastAPI Mapping

- Endpoints: Products, Orders, Reports, Admin implemented under /api with parity to Spring controllers.
- Problem-Details: 400/404/409/502 via app/utils/problem_details.py aligned to Java titles/types.
- Orders: Validation, stock check, discount via services/discount_service.py, atomic stock decrement, persisted Order/OrderItem.
- Idempotency: Table idempotency_records with key, request_hash (canonical body), response_body, status_code, created_at; logic in services/order_service.py.
- Payments: Deterministic by default; authorize with one retry on 5xx; 4xx mapped to domain error; dev fault injection POST /_admin/payment/next_failure?code=500; mock payment under /mock.
- Scheduler: Inventory (2 AM) and Loyalty (every 30 min) in tasks/scheduler.py; manual triggers in admin router; idempotent loyalty using IdempotencyRecord with LOYALTY_{orderId}.
- Reporting: /api/reports uses joinedload/selectinload to avoid N+1 (see services/report_service.py).
- Config: .env.example and YAML/ENV via app/config.py; SQLite default; Postgres supported via DATABASE_URL.
- Alembic: Schema-only migrations (alembic/versions/0001_initial.py); no data in migrations.
- Seeding: app/db/seed.py gated by APP_ENV=test or SEED=true; inserts baseline products only.
- Tests: pytest suite in fastapi_legacyshop/tests covers idempotency (201 then 200/208), conflict (409), payment retry proof, reports pagination.

Evidence
- pytest -q summary: 5 passed (see PR description).
- Idempotency curls (README and scripts/curl-examples.sh): repeat POST with same Idempotency-Key returns identical body with 200/208 after initial 201.
- Retry proof: call /_admin/payment/next_failure?code=500 then authorize-payment; logs show exactly one retry (see services/payment_service.py retry branch).
- Reporting N+1 avoidance: report_service uses joinedload to fetch related items/products in one round-trip.
