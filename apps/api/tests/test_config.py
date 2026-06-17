"""Settings load from the environment and fail fast when required values are missing."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from jobhunter.core.config import Settings


def test_missing_required_config_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(ValidationError):
        # _env_file=None so a developer's local .env can't mask the missing vars.
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/jh")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")
    monkeypatch.setenv("ENVIRONMENT", "production")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.redis_url == "redis://cache:6379/0"
    assert settings.is_production is True


def test_postgres_dsn_strips_sqlalchemy_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/jh")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.postgres_dsn == "postgresql://u:p@db:5432/jh"
