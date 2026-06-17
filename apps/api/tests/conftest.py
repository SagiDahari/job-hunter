"""Shared test fixtures.

Required settings are seeded into the environment *before* importing the app, because
``jobhunter.main`` builds the ASGI ``app`` at import time (so ``uvicorn jobhunter.main:app``
works). ``setdefault`` lets CI's real values win when they are present.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "test")

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from jobhunter.core.config import get_settings
from jobhunter.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient over a freshly built app bound to the test settings."""
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()
