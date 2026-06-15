# PR Batch 01 — Foundation

This batch establishes the skeleton everything else builds on: the monorepo, local dev
environment, CI, the FastAPI + Next.js shells, the database with pgvector, and end-to-end
authentication. It maps to **Phase 0 + Phase 1** of the MVP roadmap.

**Goal of the batch:** a user can register, verify their email, log in, and land on an
authenticated (empty) dashboard — all running locally via `docker-compose up` and green in CI.

**Related docs:** [Architecture Decisions](../architecture/decisions.md)

---

## How we work (PR conventions)

- **One PR = one reviewable unit.** Target < ~400 lines of diff where practical.
- **Branch naming:** `batch-01/pr-00X-short-slug` (e.g. `batch-01/pr-005-db-pgvector`).
- **Every PR must:** pass CI, include tests for new logic, update docs if behavior/contract
  changes, and have its row in the tracking table below moved to the right status.
- **Conventional commits** for titles: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `ci:`.
- **Definition of Done** for every PR: code + tests green, reviewer checklist complete,
  no new lint/type errors, docs updated, merged to `main`.
- A PR is not started until its **dependencies** (below) are merged.

**Status legend:** ⬜ Todo · 🟦 In progress · 🟨 In review · ✅ Merged · ⛔ Blocked

---

## Batch tracking table

| PR | Title | Depends on | Status | Owner | Reviewer |
|----|-------|------------|--------|-------|----------|
| PR-001 | Monorepo scaffolding & tooling | — | ✅ | sagi | sagi |
| PR-002 | Local dev environment (Docker Compose) | PR-001 | 🟦 | sagi | |
| PR-003 | CI pipeline (lint, type-check, test) | PR-001 | ⬜ | | |
| PR-004 | FastAPI app skeleton + settings/config | PR-001, PR-002 | ⬜ | | |
| PR-005 | Database: Postgres + pgvector + Alembic + base | PR-004 | ⬜ | | |
| PR-006 | User model + migration | PR-005 | ⬜ | | |
| PR-007 | Auth: registration & login (JWT access) | PR-006 | ⬜ | | |
| PR-008 | Auth: refresh tokens, email verify, password reset | PR-007 | ⬜ | | |
| PR-009 | Next.js app skeleton + shadcn/ui + layout | PR-001 | ⬜ | | |
| PR-010 | OpenAPI typed client + auth pages wired E2E | PR-008, PR-009 | ⬜ | | |

**Critical path:** 001 → 002 → 004 → 005 → 006 → 007 → 008 → 010.
PR-003 and PR-009 can run in parallel off PR-001.

---

## PR details

### PR-001 — Monorepo scaffolding & tooling
**Scope.** Repo layout per ADR-001: `apps/web`, `apps/api`, `packages/shared-types`,
`infra/`, `docs/`. Root tooling: `.editorconfig`, `.gitignore`, root README, license,
Python tooling (`ruff`, `mypy`, `pytest` config via `pyproject.toml`), JS tooling
(`eslint`, `prettier`, `tsconfig` base). Wire `scripts/preflight.sh` (already in repo) as
the git `pre-commit` hook.

**Acceptance criteria.**
- [x] Directory structure matches ADR-001.
- [x] `ruff`, `mypy`, `eslint`, `prettier` run from the repo root. *(configs in place + `make`
      targets; run after `make setup` installs deps)*
- [x] `scripts/preflight.sh` runs all quality gates and is installed as the `pre-commit` hook
      (or via the `pre-commit` framework) and documented in README.
- [x] Root README explains layout and how to get started.

> **Quality gate:** `scripts/preflight.sh` runs the linter, formatter check, type checker,
> and tests for every app present, and must pass before any PR in this batch is committed.
> Use `scripts/preflight.sh --fix` to autofix formatting first. See the script's `--help`.

**Review checklist.**
- [x] No app code yet — scaffolding only.
- [x] Tool configs are shared/consistent across apps.

---

### PR-002 — Local dev environment (Docker Compose)
**Scope.** `infra/compose/docker-compose.yml` with Postgres (pgvector image), Redis, and
service stubs for `api`. `.env.example`. Makefile / task runner targets (`make up`,
`make down`, `make logs`).

**Acceptance criteria.**
- [ ] `docker-compose up` starts Postgres (with pgvector available) and Redis.
- [ ] `.env.example` documents every required variable; no secrets committed.
- [ ] Healthchecks defined for Postgres and Redis.
- [ ] README section: "Run locally".

**Review checklist.**
- [ ] pgvector extension image used (not vanilla postgres).
- [ ] Named volumes for data persistence.

---

### PR-003 — CI pipeline (lint, type-check, test)
**Scope.** `.github/workflows/ci.yml`. Path-aware jobs (ADR-001): backend job (ruff, mypy,
pytest with a Postgres+Redis service container), frontend job (eslint, tsc, build).

**Acceptance criteria.**
- [ ] PRs trigger lint + type-check + tests for the changed app only.
- [ ] Backend tests run against a real Postgres+pgvector service container.
- [ ] CI fails on lint/type/test errors.
- [ ] Status badge in README.

**Review checklist.**
- [ ] No secrets in workflow; uses GitHub OIDC/secrets where needed.
- [ ] Caching configured for deps (pip, npm).

---

### PR-004 — FastAPI app skeleton + settings/config
**Scope.** ASGI app, `core/config.py` (Pydantic Settings from env), structured logging with
correlation IDs, `/health` and `/ready` endpoints, OpenAPI metadata, layered package
structure per ADR-003 (`api/`, `services/`, `domain/`, `repositories/` empty shells).

**Acceptance criteria.**
- [ ] `GET /health` returns 200; `GET /ready` checks DB + Redis connectivity.
- [ ] Settings load from env; fail fast on missing required config.
- [ ] Structured JSON logs with request correlation IDs.
- [ ] Layer directories exist with module boundaries documented.

**Review checklist.**
- [ ] No business logic in `api/` routers.
- [ ] `domain/` has zero framework imports.

---

### PR-005 — Database: Postgres + pgvector + Alembic + base
**Scope.** SQLAlchemy session/engine, declarative base, Alembic configured, first migration
enabling the `pgvector` extension and `citext`. Repository base class. Test fixtures spinning
up a clean DB per test.

**Acceptance criteria.**
- [ ] `alembic upgrade head` enables pgvector + citext and runs in CI.
- [ ] DB session dependency wired into FastAPI.
- [ ] Repository base + a smoke test proving a round-trip insert/select.
- [ ] Migration is reversible (`downgrade` works).

**Review checklist.**
- [ ] Connection pooling configured.
- [ ] No raw SQL outside repositories/migrations (ADR-003).

---

### PR-006 — User model + migration
**Scope.** `users` table per schema (uuid pk, citext email unique, hashed_password,
full_name, is_active, is_verified, timestamps). Domain `User` model, `UserRepository`,
migration, tests.

**Acceptance criteria.**
- [ ] Migration creates `users` with a unique citext email index.
- [ ] `UserRepository` supports create / get_by_email / get_by_id.
- [ ] Unit tests for the repository against the test DB.

**Review checklist.**
- [ ] Email uniqueness enforced at the DB level, not just app level.
- [ ] No password hashing logic here (lives in auth service, PR-007).

---

### PR-007 — Auth: registration & login (JWT access)
**Scope.** Register + login endpoints. Argon2id hashing (ADR-009). JWT access token issue +
verify. `get_current_user` dependency. Pydantic request/response schemas. Rate limiting on
auth endpoints (Redis).

**Acceptance criteria.**
- [ ] Register creates an inactive/unverified user, hashes password with Argon2id.
- [ ] Login returns a short-lived (~15 min) JWT access token on valid credentials.
- [ ] Protected test endpoint rejects missing/invalid/expired tokens.
- [ ] Rate limiting on register/login verified by a test.
- [ ] Integration tests cover the happy path + invalid-credential path.

**Review checklist.**
- [ ] Passwords never logged or returned.
- [ ] Generic error on bad login (no user-enumeration leak).
- [ ] Every protected query scoped by `user_id`.

---

### PR-008 — Auth: refresh tokens, email verify, password reset
**Scope.** Rotating refresh tokens in httpOnly+secure cookies with reuse detection (ADR-009).
Email verification + password-reset flows with single-use, expiring tokens. Email send
stubbed/console in dev (SES wired later). CSRF protection for cookie auth.

**Acceptance criteria.**
- [ ] Refresh endpoint rotates the token; reuse of an old token is detected and rejected.
- [ ] Email verification activates the account via a single-use, expiring token.
- [ ] Password reset issues + consumes a single-use, expiring token.
- [ ] CSRF protection present on cookie-authenticated routes.
- [ ] Tests cover rotation, reuse-detection, verify, and reset flows.

**Review checklist.**
- [ ] Tokens are single-use and expiring; no token values logged.
- [ ] Refresh cookie is httpOnly, secure, SameSite set.

---

### PR-009 — Next.js app skeleton + shadcn/ui + layout
**Scope.** Next.js (App Router, TS), Tailwind, shadcn/ui init, base layout, theme, a public
landing page and an empty protected `/dashboard` route. Frontend lint/build green in CI.

**Acceptance criteria.**
- [ ] App builds and runs; landing + dashboard routes render.
- [ ] shadcn/ui components installed and themed.
- [ ] `/dashboard` is gated (redirect to login when unauthenticated — stubbed until PR-010).
- [ ] Lighthouse/build passes in CI.

**Review checklist.**
- [ ] Tailwind + shadcn conventions consistent.
- [ ] No hardcoded API URLs (env-driven).

---

### PR-010 — OpenAPI typed client + auth pages wired E2E
**Scope.** Generate `packages/shared-types` from the API OpenAPI schema. Typed API client in
`apps/web/lib/api`. Register / login / verify / reset pages wired to the real backend. Full
local E2E: register → verify → login → see dashboard.

**Acceptance criteria.**
- [ ] TS types generated from OpenAPI; generation is a repeatable command in CI.
- [ ] Register/login/verify/reset pages call the real API and handle errors.
- [ ] Auth state persists across reload (access token refresh works).
- [ ] One E2E test (Playwright) covering register → login → dashboard.

**Review checklist.**
- [ ] No `any` types leaking from the API client.
- [ ] Tokens stored per ADR-009 (refresh in httpOnly cookie, not localStorage).

---

## Batch exit criteria (Definition of Done for Batch 01)

- [ ] All 10 PRs merged to `main`.
- [ ] `docker-compose up` brings the full stack up locally.
- [ ] CI green on `main` (lint, type-check, backend + frontend tests, E2E).
- [ ] A new user can register → verify → log in → reach the dashboard, end to end.
- [ ] ADRs referenced by these PRs are still accurate (or updated/superseded).

**Next batch preview — Batch 02 (Profile):** CV upload to S3, Claude-based CV parsing +
skill extraction, preferences UI/API, and the embedding pipeline foundation.
