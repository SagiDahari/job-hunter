"""HTTP middleware: request correlation ids + structured access logs."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from jobhunter.core.context import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"

_logger = logging.getLogger("jobhunter.access")

Handler = Callable[[Request], Awaitable[Response]]


async def request_context_middleware(request: Request, call_next: Handler) -> Response:
    """Bind a correlation id to the request and emit one access log line.

    Reuses an inbound ``X-Request-ID`` (e.g. from a load balancer) when present so a
    trace can be followed across services, otherwise mints a new one. The id is echoed
    back on the response and attached to every log record produced while handling it.
    """
    request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
    token = request_id_var.set(request_id)
    start = time.perf_counter()

    try:
        try:
            response = await call_next(request)
        except Exception:
            # Logged while the correlation id is still bound to the context.
            _logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        _logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
        return response
    finally:
        request_id_var.reset(token)
