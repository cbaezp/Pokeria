"""Standard error formatting and exception handlers."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import correlation_id_ctx, get_logger
from app.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    PermissionDeniedError,
)
from app.domain.exceptions import (
    ValidationError as DomainValidationError,
)

logger = get_logger(__name__)


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Construct standard error JSON response."""
    request_id = correlation_id_ctx.get() or "unknown"
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": request_id,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        logger.info(f"Entity not found: {exc.message}")
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError) -> JSONResponse:
        logger.info(f"Duplicate entity conflict: {exc.message}")
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(
        request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        logger.warning(f"Permission denied: {exc.message}")
        return create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(
        request: Request, exc: DomainValidationError
    ) -> JSONResponse:
        logger.info(f"Domain validation error: {exc.message}")
        return create_error_response(
            status_code=422,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning(f"Domain error: {exc.message}")
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info(f"Request validation error: {exc.errors()}")
        return create_error_response(
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message="Invalid request payload or parameters",
            details=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled server error: {exc}")
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred while processing the request",
        )
