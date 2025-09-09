from fastapi import FastAPI
from .routers import products, orders, reports, admin, mock_payment, dev_inject
from .utils.problem_details import register_problem_handlers

app = FastAPI(title="LegacyShop FastAPI")

app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(mock_payment.router)
app.include_router(dev_inject.router)

register_problem_handlers(app)
