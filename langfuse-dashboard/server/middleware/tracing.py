"""
TracingMiddleware
-----------------
Attaches a unique request-id and session-id to every incoming HTTP request and
injects it into the structlog context so that every log line emitted during
that request automatically carries the trace metadata.
"""
from __future__ import annotations
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger()


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        session_id = request.headers.get("x-session-id", str(uuid.uuid4()))

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            session_id=session_id,
            path=request.url.path,
            method=request.method,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info(
                "request",
                status=response.status_code,
                latency_ms=elapsed_ms,
            )
            response.headers["x-request-id"] = request_id
            return response
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.error("request_error", error=str(exc), latency_ms=elapsed_ms)
            raise
