"""The JSON log formatter emits parseable records carrying the correlation id."""

from __future__ import annotations

import json
import logging

from jobhunter.core.context import request_id_var
from jobhunter.core.logging import JsonFormatter


def _record(**overrides: object) -> logging.LogRecord:
    return logging.makeLogRecord({"name": "test", "levelname": "INFO", "msg": "hello", **overrides})


def test_formats_record_as_json() -> None:
    payload = json.loads(JsonFormatter().format(_record()))
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    assert "timestamp" in payload


def test_includes_request_id_when_in_scope() -> None:
    token = request_id_var.set("trace-xyz")
    try:
        payload = json.loads(JsonFormatter().format(_record()))
    finally:
        request_id_var.reset(token)
    assert payload["request_id"] == "trace-xyz"


def test_omits_request_id_outside_request_scope() -> None:
    payload = json.loads(JsonFormatter().format(_record()))
    assert "request_id" not in payload


def test_surfaces_structured_extras() -> None:
    payload = json.loads(JsonFormatter().format(_record(job_id=42)))
    assert payload["job_id"] == 42
