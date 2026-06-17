# JobHunter API

FastAPI backend for JobHunter AI. Python 3.12, layered architecture
([ADR-003](../../docs/architecture/decisions.md#adr-003-layered-architecture-domain--service--repository)).

## Layout

```
src/jobhunter/
  main.py         ASGI app factory (create_app / app)
  core/           config, structured logging, request context, middleware
  api/            HTTP routers (thin, request/response only)
  services/       use-case orchestration
  domain/         pure business models/rules (no framework imports)
  repositories/   data access per aggregate      # populated in PR-005+
tests/            unit / integration / e2e
pyproject.toml    deps + ruff / mypy / pytest config
```

## Configuration

Settings load from the environment via `pydantic-settings` (`core/config.py`). Required
variables (`DATABASE_URL`, `REDIS_URL`) have no defaults — a missing one fails fast at
startup. See the repo-root `.env.example`.

## Endpoints

| Method | Path            | Purpose                                                        |
| ------ | --------------- | -------------------------------------------------------------- |
| GET    | `/health`       | Liveness — process is up; touches no dependencies.             |
| GET    | `/ready`        | Readiness — 200 when Postgres + Redis are reachable, else 503. |
| GET    | `/docs`         | Swagger UI.                                                    |
| GET    | `/openapi.json` | OpenAPI schema.                                                |

Every response carries an `X-Request-ID` correlation header (echoed from the request when
provided), and logs are emitted as one JSON object per line carrying that id.

## Develop

```bash
uv sync                                  # install deps + dev tools
uv run uvicorn jobhunter.main:app --reload   # run locally (needs DATABASE_URL, REDIS_URL)
uv run ruff check .                      # lint
uv run ruff format .                     # format
uv run mypy .                            # type-check
uv run pytest                            # tests
```

Or from the repo root: `make api-check` (runs all gates via `scripts/preflight.sh`), and
`make up` to run the API in the Docker stack alongside Postgres + Redis.
