import logging

from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.errors import (
    integrity_error_handler,
    database_error_handler,
    unexpected_error_handler,
)

from app.core.database import engine
from app.api.auth import router as auth_router
from app.api.organization import router as organization_router
from app.api.member import router as member_router
from app.api.invitation import router as invitation_router
from app.api.product import router as product_router
from app.api.inventory import router as inventory_router
from app.api.customer import router as customer_router
from app.api.order import router as order_router
from app.api.dashboard import router as dashboard_router

app = FastAPI(
    title="Multi-Tenant Business Operations SaaS",
    version="1.0.0"
)

app.add_exception_handler(
    IntegrityError,
    integrity_error_handler
)

app.add_exception_handler(
    SQLAlchemyError,
    database_error_handler
)

app.add_exception_handler(
    Exception,
    unexpected_error_handler
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY
)

app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(member_router)
app.include_router(invitation_router)
app.include_router(product_router)
app.include_router(inventory_router)
app.include_router(customer_router)
app.include_router(order_router)
app.include_router(dashboard_router)

@app.get("/")
def root():
    return {
        "message": "Multi-Tenant Business Operations API is running"
    }

@app.get("/health/db")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "connected"
    }