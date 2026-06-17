"""Readiness checks for the service's backing dependencies.

Orchestration only (ADR-003): routers call :func:`check_readiness`; the actual
SQLAlchemy/Redis wiring is replaced with shared engines/pools in later PRs.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass

import psycopg
import redis.asyncio as redis

from jobhunter.core.config import Settings

_logger = logging.getLogger(__name__)

# A dependency that hangs is as bad as one that's down — bound every probe.
_PROBE_TIMEOUT_S = 3.0


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    """Aggregate readiness across dependencies."""

    checks: dict[str, bool]

    @property
    def ready(self) -> bool:
        return all(self.checks.values())


async def _check_postgres(settings: Settings) -> bool:
    try:
        async with await asyncio.wait_for(
            psycopg.AsyncConnection.connect(settings.postgres_dsn),
            timeout=_PROBE_TIMEOUT_S,
        ) as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        _logger.warning("postgres readiness probe failed", exc_info=True)
        return False


async def _check_redis(settings: Settings) -> bool:
    client = None
    try:
        client = redis.from_url(settings.redis_url)
        return bool(await asyncio.wait_for(client.ping(), timeout=_PROBE_TIMEOUT_S))
    except Exception:
        _logger.warning("redis readiness probe failed", exc_info=True)
        return False
    finally:
        if client is not None:
            with contextlib.suppress(Exception):
                await client.aclose()


async def check_readiness(settings: Settings) -> ReadinessReport:
    """Probe every dependency concurrently and report per-component status."""
    postgres_ok, redis_ok = await asyncio.gather(
        _check_postgres(settings),
        _check_redis(settings),
    )
    return ReadinessReport(checks={"postgres": postgres_ok, "redis": redis_ok})
