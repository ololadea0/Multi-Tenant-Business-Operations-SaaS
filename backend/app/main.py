from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

from app.core.database import engine
from app.api.auth import router as auth_router
from app.api.organization import router as organization_router
from app.api.member import router as member_router
from app.api.invitation import router as invitation_router

app = FastAPI(
    title="Multi-Tenant Business Operations SaaS",
    version="1.0.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY
)

app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(member_router)
app.include_router(invitation_router)

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