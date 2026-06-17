"""Tests for liveness, readiness, and request correlation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jobhunter import __version__
from jobhunter.api import health
from jobhunter.core.middleware import REQUEST_ID_HEADER
from jobhunter.services.health import ReadinessReport


def test_health_is_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_health_does_not_touch_dependencies(client: TestClient) -> None:
    # No DB/Redis are running in unit tests; liveness must still succeed.
    response = client.get("/health")
    assert response.status_code == 200


def test_response_carries_correlation_id(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers[REQUEST_ID_HEADER]


def test_inbound_correlation_id_is_echoed(client: TestClient) -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "trace-123"})
    assert response.headers[REQUEST_ID_HEADER] == "trace-123"


def test_ready_returns_200_when_all_dependencies_up(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _all_ok(_settings: object) -> ReadinessReport:
        return ReadinessReport(checks={"postgres": True, "redis": True})

    monkeypatch.setattr(health, "check_readiness", _all_ok)

    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True, "checks": {"postgres": True, "redis": True}}


def test_ready_returns_503_when_a_dependency_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _redis_down(_settings: object) -> ReadinessReport:
        return ReadinessReport(checks={"postgres": True, "redis": False})

    monkeypatch.setattr(health, "check_readiness", _redis_down)

    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"ready": False, "checks": {"postgres": True, "redis": False}}
