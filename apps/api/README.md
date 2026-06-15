# JobHunter API

FastAPI backend for JobHunter AI. Python 3.12, layered architecture
([ADR-003](../../docs/architecture/decisions.md#adr-003-layered-architecture-domain--service--repository)).

## Layout

```
src/jobhunter/
  api/            HTTP routers (thin)            # added in PR-004+
  services/       use-case orchestration         # added in PR-004+
  domain/         pure business models/rules     # added in PR-004+
  repositories/   data access per aggregate      # added in PR-005+
tests/            unit / integration / e2e
pyproject.toml    deps + ruff / mypy / pytest config
```

## Develop

```bash
uv sync                 # install deps + dev tools (ruff, mypy, pytest)
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy .           # type-check
uv run pytest           # tests
```

Or from the repo root: `make api-check` (runs all of the above via `scripts/preflight.sh`).
