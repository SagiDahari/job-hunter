# JobHunter AI

AI-powered job matching for junior and mid-level software engineers. Users upload a CV and
set preferences; the platform ingests job postings from multiple sources, scores them against
the user with a hybrid vector + LLM pipeline, surfaces missing skills, and emails a daily
digest of high-match opportunities.

> **Status:** early development — building out [Batch 01 (Foundation)](docs/pull-requests/batch-01-foundation.md).

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js · TypeScript · Tailwind · shadcn/ui |
| Backend | FastAPI · Python 3.12 |
| Data | PostgreSQL · pgvector |
| Jobs | Redis · Celery |
| AI | Claude (reasoning) · Voyage (embeddings) — see [ADR-004](docs/architecture/decisions.md#adr-004-ai-providers--claude-for-reasoning-voyage-for-embeddings) |
| Infra | Docker · AWS (ECS Fargate, Terraform) |

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

Prerequisites: Python 3.12, Node 20+, and (recommended) [`uv`](https://docs.astral.sh/uv/)
for Python deps. Docker for the local stack (added in PR-002).

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

## Development workflow

We deliver work as small, reviewed PRs tracked in `docs/pull-requests/`. Each PR:

- branches as `batch-01/pr-00X-short-slug`,
- uses Conventional Commit titles (`feat:`, `fix:`, `chore:`, …),
- must pass `scripts/preflight.sh` before commit,
- updates its row in the batch tracking table.

## Documentation

- [Architecture Decision Records](docs/architecture/decisions.md)
- [PR Batch 01 — Foundation](docs/pull-requests/batch-01-foundation.md)

## License

[MIT](LICENSE) © 2026 Sagi Dahari
