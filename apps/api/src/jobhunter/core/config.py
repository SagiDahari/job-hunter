"""Application settings, loaded from the environment (12-factor).

Required values have no default, so a missing one fails fast at startup with a
clear ``ValidationError`` rather than surfacing as a confusing runtime error later.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Strongly-typed application configuration.

    Field names map to upper-cased environment variables (e.g. ``database_url`` ←
    ``DATABASE_URL``). Real environment variables take precedence over the ``.env``
    file, which is only a developer convenience.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "JobHunter API"
    environment: Environment = "development"
    log_level: str = "INFO"

    # Required — no defaults, so the app refuses to start without them.
    database_url: str
    redis_url: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def postgres_dsn(self) -> str:
        """A libpq-style DSN for direct ``psycopg`` connections.

        ``DATABASE_URL`` uses SQLAlchemy's ``postgresql+psycopg://`` scheme (the ORM
        lands in PR-005); psycopg itself wants a plain ``postgresql://`` URL.
        """
        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so the environment is parsed once. Call ``get_settings.cache_clear()`` in
    tests that need to re-read a patched environment.
    """
    return Settings()  # type: ignore[call-arg]  # values come from the environment
