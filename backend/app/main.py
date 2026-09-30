from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.api.auth import router as auth_router

app = FastAPI(
    title="Multi-Tenant Business Operations SaaS",
    version="1.0.0"
)

app.include_router(auth_router)


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