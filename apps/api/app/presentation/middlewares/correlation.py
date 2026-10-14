"""Correlation ID middleware for end-to-end request tracing."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_ctx

HEADER_NAME = "X-Request-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates a unique correlation ID for every HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        header_val = request.headers.get(HEADER_NAME)
        correlation_id = header_val.strip() if header_val else str(uuid.uuid4())

        # Set context variable for structured logging
        token = correlation_id_ctx.set(correlation_id)
        # Store on request state for endpoint handlers
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
            response.headers[HEADER_NAME] = correlation_id
            return response
        finally:
            correlation_id_ctx.reset(token)
