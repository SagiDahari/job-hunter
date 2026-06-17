"""Per-request context propagated via :mod:`contextvars`.

Lets any code (log records, services) read the current request's correlation id
without threading it through every call signature.
"""

from __future__ import annotations

from contextvars import ContextVar

# Empty string means "no request in scope" (e.g. startup, background tasks).
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the correlation id bound to the current request, or ``""``."""
    return request_id_var.get()
