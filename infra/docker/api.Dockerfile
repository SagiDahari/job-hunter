# syntax=docker/dockerfile:1
#
# JobHunter API image. Build context is apps/api (see infra/compose/docker-compose.yml).
# Uses the uv base image so dependency installs are fast, locked, and reproducible.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first, against the lockfile only, for a cacheable layer that
# is invalidated solely by dependency changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Then the application source + install the project itself.
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Create non-root user for security.
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "jobhunter.main:app", "--host", "0.0.0.0", "--port", "8000"]
