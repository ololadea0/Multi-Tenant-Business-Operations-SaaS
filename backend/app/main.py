import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.errors import (
    http_exception_handler,
    integrity_error_handler,
    database_error_handler,
    request_validation_exception_handler,
    unexpected_error_handler,
)

from app.core.database import engine
from app.api.auth import router as auth_router
from app.api.platform_organization import router as organization_router
from app.api.platform_member import router as member_router
from app.api.invitations import router as invitation_router, public_router as public_invitation_router
from app.api.products import router as product_router
from app.api.platform_inventory import router as inventory_router, summary_router
from app.api.platform_customer import router as customer_router
from app.api.orders import router as order_router
from app.api.activity import router as activity_router
from app.api.dashboard import router as dashboard_router
from app.api.sync import router as sync_router
from app.api.platform_billing import router as billing_router
from app.api.platform_admin import router as admin_router
from app.api.notifications import router as notifications_router
from app.services.billing import start_billing_worker, stop_billing_worker

app = FastAPI(
    title="Multi-Tenant Business Operations SaaS",
    version="1.0.0"
)

app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    request_validation_exception_handler,
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

allowed_origins = [
    origin.strip()
    for origin in settings.CORS_ALLOW_ORIGINS.split(",")
    if origin.strip()
]

if not allowed_origins or allowed_origins == ["*"]:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY
)

app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(member_router)
app.include_router(invitation_router)
app.include_router(public_invitation_router)
app.include_router(product_router)
app.include_router(inventory_router)
app.include_router(summary_router)
app.include_router(customer_router)
app.include_router(order_router)
app.include_router(activity_router)
app.include_router(dashboard_router)
app.include_router(sync_router)
app.include_router(billing_router)
app.include_router(admin_router)
app.include_router(notifications_router)

@app.on_event("startup")
def startup_event():
    start_billing_worker()

@app.on_event("shutdown")
def shutdown_event():
    stop_billing_worker()

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
