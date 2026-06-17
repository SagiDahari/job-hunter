"""HTTP API layer (ADR-003): routers only — thin request/response handling.

No business logic lives here; routers delegate to ``services``. ``api_router``
aggregates every router for the app factory to mount under the API prefix.
"""

from fastapi import APIRouter

from jobhunter.api import health

api_router = APIRouter()
api_router.include_router(health.router)

__all__ = ["api_router"]
