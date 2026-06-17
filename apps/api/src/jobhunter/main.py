"""Application entry point: the ASGI app factory.

Run in development with::

    uv run uvicorn jobhunter.main:app --reload
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from jobhunter import __version__
from jobhunter.api import api_router
from jobhunter.core.config import Settings, get_settings
from jobhunter.core.logging import configure_logging
from jobhunter.core.middleware import request_context_middleware

_DESCRIPTION = "AI-powered job matching — backend API."


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Reading settings here means a missing required variable aborts startup with a
    clear error (fail fast) instead of failing on the first request.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=_DESCRIPTION,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Correlation ids + access logging wrap every request.
    app.middleware("http")(request_context_middleware)

    app.include_router(api_router)

    logging.getLogger(__name__).info(
        "application configured",
        extra={"environment": settings.environment, "version": __version__},
    )
    return app


app = create_app()
