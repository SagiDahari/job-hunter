"""Liveness and readiness endpoints.

Thin handlers (ADR-003): ``/ready`` delegates the actual probing to the health
service and only maps the result onto an HTTP status code.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from jobhunter import __version__
from jobhunter.core.config import Settings, get_settings
from jobhunter.services.health import check_readiness

router = APIRouter(tags=["health"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, bool]


@router.get("/health", summary="Liveness probe")
async def health() -> HealthResponse:
    """Process is up and serving — does not touch external dependencies."""
    return HealthResponse(status="ok", version=__version__)


@router.get(
    "/ready",
    summary="Readiness probe",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def ready(settings: SettingsDep, response: Response) -> ReadinessResponse:
    """Ready to serve traffic only when every backing dependency is reachable."""
    report = await check_readiness(settings)
    if not report.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(ready=report.ready, checks=report.checks)
