# JobHunter AI

[![CI](https://github.com/SagiDahari/job-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/SagiDahari/job-hunter/actions/workflows/ci.yml)

AI-powered job matching for junior and mid-level software engineers. Users upload a CV and
set preferences; the platform ingests job postings from multiple sources, scores them against
the user with a hybrid vector + LLM pipeline, surfaces missing skills, and emails a daily
digest of high-match opportunities.

> **Status:** early development — building out [Batch 01 (Foundation)](docs/pull-requests/batch-01-foundation.md).

## Tech stack

| Layer    | Choice                                                                                                                                                    |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend | Next.js · TypeScript · Tailwind · shadcn/ui                                                                                                               |
| Backend  | FastAPI · Python 3.12                                                                                                                                     |
| Data     | PostgreSQL · pgvector                                                                                                                                     |
| Jobs     | Redis · Celery                                                                                                                                            |
| AI       | Claude (reasoning) · Voyage (embeddings) — see [ADR-004](docs/architecture/decisions.md#adr-004-ai-providers--claude-for-reasoning-voyage-for-embeddings) |
| Infra    | Docker · AWS (ECS Fargate, Terraform)                                                                                                                     |

## Repository layout

```
apps/
  api/              FastAPI backend (layered: api / services / domain / repositories)
  web/              Next.js frontend
packages/
  shared-types/     TypeScript types generated from the API OpenAPI schema
infra/
  docker/           Dockerfiles per service
  terraform/        AWS infrastructure as code
  compose/          local docker-compose stack
docs/
  architecture/     Architecture Decision Records (ADRs)
  pull-requests/    PR batch plans & tracking
scripts/
  preflight.sh      quality-gate runner (lint · format · type-check · test)
```

See [ADR-001](docs/architecture/decisions.md#adr-001-monorepo-with-apps-and-shared-packages)
for why this is a monorepo and [ADR-003](docs/architecture/decisions.md#adr-003-layered-architecture-domain--service--repository)
for the backend layering.

## Getting started

Prerequisites: Python 3.12, Node 20+, Docker (with Compose), and (recommended)
[`uv`](https://docs.astral.sh/uv/) for Python deps.

```bash
# install dev tooling for whichever apps exist
make setup

# run all quality gates (lint, format check, type-check, tests)
make check

# autofix formatting/lint, then re-check
make fix
```

A `pre-commit` git hook runs `scripts/preflight.sh` automatically on every commit.
Bypass in an emergency with `git commit --no-verify`.

## Run locally

The local stack runs PostgreSQL (with pgvector) and Redis via Docker Compose.

```bash
cp .env.example .env     # local dev defaults — safe to use as-is
make up                  # start Postgres + Redis in the background
make ps                  # check container health
make logs                # tail logs
make down                # stop (data is kept in named volumes)
```

| Service               | Host port (default) | Purpose               |
| --------------------- | ------------------- | --------------------- |
| PostgreSQL + pgvector | `5432`              | primary datastore     |
| Redis                 | `6379`              | Celery broker + cache |

Connection strings for the app live in `.env` (`DATABASE_URL`, `REDIS_URL`). The API and
worker services join this stack in later PRs (api in PR-004).

## Development workflow

We deliver work as small, reviewed PRs tracked in `docs/pull-requests/`. Each PR:

- branches as `batch-01/pr-00X-short-slug`,
- uses Conventional Commit titles (`feat:`, `fix:`, `chore:`, …),
- must pass `scripts/preflight.sh` before commit,
- updates its row in the batch tracking table.

### Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main` and on every PR.
It is **path-aware** (ADR-001): the backend job runs only when `apps/api/**` changes, the
frontend job only when web/shared/root tooling changes.

- **Backend** — `ruff` (format + lint), `mypy`, and `pytest` against a real
  `pgvector/pgvector:pg16` Postgres plus a Redis service container. Deps installed with
  `uv` from the committed `uv.lock` and cached between runs.
- **Frontend** — `prettier` and `eslint` over the repo; `tsc` and the Next.js build run
  once `apps/web` exists (PR-009). `npm` deps are cached via the committed `package-lock.json`.

A single aggregate `ci` job summarizes the run so branch protection can require one status
check regardless of which paths changed.

## Documentation

- [Architecture Decision Records](docs/architecture/decisions.md)
- [PR Batch 01 — Foundation](docs/pull-requests/batch-01-foundation.md)

## License

[MIT](LICENSE) © 2026 Sagi Dahari
