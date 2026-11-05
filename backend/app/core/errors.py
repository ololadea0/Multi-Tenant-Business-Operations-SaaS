import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


logger = logging.getLogger(__name__)


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation failed",
            "errors": [
                {
                    "loc": list(error.get("loc", [])),
                    "msg": error.get("msg"),
                    "type": error.get("type"),
                }
                for error in exc.errors()
            ],
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError
):
    logger.exception(
        "Database integrity error on %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=409,
        content={
            "detail": "The request conflicts with existing data or violates a database rule."
        }
    )


async def database_error_handler(
    request: Request,
    exc: SQLAlchemyError
):
    logger.exception(
        "Database error on %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred. Please try again later."
        }
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception
):
    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later."
        }
    )