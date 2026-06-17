"""Structured (JSON) logging.

One JSON object per line so log aggregators (CloudWatch, etc.) can parse fields
directly. Every record carries the current request's correlation id when one is in
scope. Kept dependency-free — no third-party log libraries.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from jobhunter.core.context import get_request_id

# Attributes present on every ``logging.LogRecord``; anything else a caller passes
# via ``extra=`` is treated as a custom field worth emitting.
_RESERVED = set(
    logging.makeLogRecord({}).__dict__.keys(),
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Surface structured extras (logger.info("...", extra={"job_id": 5})).
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # uvicorn ships its own handlers; let ours format their records instead.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
