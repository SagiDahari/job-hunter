# JobHunter AI — Architecture Decision Records (ADR)

This document records the significant architecture decisions made for JobHunter AI.
Each decision is immutable once **Accepted** — if we change our mind, we add a new ADR
that supersedes the old one (and mark the old one **Superseded by ADR-XXX**) rather than
editing history.

**Status legend:** `Proposed` · `Accepted` · `Superseded` · `Deprecated`

| # | Title | Status |
|---|-------|--------|
| [ADR-001](#adr-001-monorepo-with-apps-and-shared-packages) | Monorepo with apps + shared packages | Accepted |
| [ADR-002](#adr-002-modular-monolith-over-microservices-for-mvp) | Modular monolith over microservices for MVP | Accepted |
| [ADR-003](#adr-003-layered-architecture-domain--service--repository) | Layered architecture (domain / service / repository) | Accepted |
| [ADR-004](#adr-004-ai-providers--claude-for-reasoning-voyage-for-embeddings) | AI providers — Claude for reasoning, Voyage for embeddings | Accepted |
| [ADR-005](#adr-005-two-stage-matching-funnel-vector--llm) | Two-stage matching funnel (vector → LLM) | Accepted |
| [ADR-006](#adr-006-postgresql--pgvector-with-hnsw-indexes) | PostgreSQL + pgvector with HNSW indexes | Accepted |
| [ADR-007](#adr-007-celery--redis-with-dedicated-queues) | Celery + Redis with dedicated queues | Accepted |
| [ADR-008](#adr-008-plugin-based-ingestion-adapters) | Plugin-based ingestion adapters | Accepted |
| [ADR-009](#adr-009-authentication--jwt-access--rotating-refresh-tokens) | Authentication — JWT access + rotating refresh tokens | Accepted |
| [ADR-010](#adr-010-aws-on-ecs-fargate-provisioned-with-terraform) | AWS on ECS Fargate, provisioned with Terraform | Accepted |

---

## ADR-001: Monorepo with apps + shared packages

**Status:** Accepted · **Date:** 2026-06-15

### Context
Frontend (Next.js/TS) and backend (FastAPI/Python) need to share a type contract.
We want atomic changes (an API change + its frontend consumer in one PR) and a single CI.

### Decision
Single Git repository. `apps/web`, `apps/api`, shared `packages/shared-types`
(TypeScript types generated from the API's OpenAPI schema), `infra/` for IaC and Docker,
`docs/` for this and other docs.

### Consequences
- ✅ Atomic cross-stack PRs; one source of truth for the API contract.
- ✅ Simpler local dev (`docker-compose up`).
- ⚠️ CI must be path-aware so a frontend-only change doesn't rebuild the backend.

---

## ADR-002: Modular monolith over microservices for MVP

**Status:** Accepted · **Date:** 2026-06-15

### Context
The domain has clear bounded contexts (Identity, Profile, Ingestion, Matching,
Notification). Microservices would demonstrate distributed-systems skill but add
operational overhead disproportionate to a solo/small-team MVP.

### Decision
Build a **modular monolith**: one deployable FastAPI app with strictly separated
internal modules. Contexts communicate through service interfaces and async events
(`cv.parsed`, `job.ingested`, `match.created`), never by reaching into each other's tables.

### Consequences
- ✅ Fast to build and deploy; cheap to run.
- ✅ Clean boundaries make later extraction (Ingestion, Matching) mechanical — see ADR-010.
- ⚠️ Requires discipline: no cross-context table access. Enforced in code review.
- Superseding path: when a context needs independent scaling, extract it into its own
  service behind an event bus.

---

## ADR-003: Layered architecture (domain / service / repository)

**Status:** Accepted · **Date:** 2026-06-15

### Context
We want testable business logic and thin HTTP handlers, and to avoid framework lock-in
leaking into core logic.

### Decision
Four layers in `apps/api`:
- **`api/`** — routers, request/response only (thin).
- **`services/`** — use-case orchestration.
- **`domain/`** — pure business models and rules, **zero framework imports**.
- **`repositories/`** — all data access, one per aggregate; the only layer that writes SQL.

### Consequences
- ✅ Domain is unit-testable without a DB or HTTP server.
- ✅ Swapping the ORM or web framework touches only edge layers.
- ⚠️ More files / indirection. Justified by testability and portfolio signal.

---

## ADR-004: AI providers — Claude for reasoning, Voyage for embeddings

**Status:** Accepted · **Date:** 2026-06-15

### Context
Two distinct AI workloads: (a) reasoning — CV parsing, skill extraction, match
explanation, gap analysis; (b) semantic similarity — embeddings for pgvector search.
Anthropic does not ship an embeddings endpoint.

### Decision
- **Reasoning:** Claude. `claude-haiku-4-5` for high-volume per-job extraction/scoring;
  `claude-opus-4-8` for the user-facing daily summary where quality is read by humans.
- **Embeddings:** Voyage AI (`voyage-3`, 1024-dim), Anthropic's recommended pairing.
  Fallback adapter for OpenAI `text-embedding-3-large` if needed.

All AI access goes through an adapter interface in `integrations/ai/` so providers are
swappable and mockable in tests.

### Consequences
- ✅ Cost-appropriate model per task; strong structured-output reliability from Claude.
- ✅ Vendor-swappable via the adapter boundary.
- ⚠️ Two vendors to manage keys/quotas for. Mitigated by per-provider rate limiting (ADR-007).
- Embedding dimension (1024) is fixed in the schema; changing providers may require re-embedding.

---

## ADR-005: Two-stage matching funnel (vector → LLM)

**Status:** Accepted · **Date:** 2026-06-15

### Context
Running an LLM over every (user × job) pair is a cost and latency bomb. We need scale
*and* quality explanations.

### Decision
- **Stage 1 (coarse, cheap):** hard-constraint SQL filter (location, remote, seniority,
  salary, employment type) → pgvector cosine search → top-K (~50) candidates. No LLM.
- **Stage 2 (precision, expensive):** one Claude call per top-N (~15) candidate produces
  structured output: `match_score`, `matched_skills`, `missing_skills`, `explanation`.
- **Final score:** weighted blend `0.4 × vector_score + 0.6 × llm_score` (tunable). Store
  both components for transparency and debugging.

### Consequences
- ✅ LLM cost scales with users × N, not users × all-jobs.
- ✅ Explainable matches + gap analysis as a product feature.
- ⚠️ Blend weights need empirical tuning; we persist component scores to enable that.

---

## ADR-006: PostgreSQL + pgvector with HNSW indexes

**Status:** Accepted · **Date:** 2026-06-15

### Context
We need relational data and vector similarity in one store for the MVP. A separate vector
DB adds operational cost we don't yet need.

### Decision
PostgreSQL with the `pgvector` extension. `HNSW` indexes (`vector_cosine_ops`) on all
embedding columns (CVs, jobs, skills). Dedup via `content_hash` unique constraints.
Partition `job_postings` by month once volume warrants.

### Consequences
- ✅ One store, transactional consistency, simple ops.
- ✅ HNSW gives better recall/latency than IVFFlat at our scale.
- ⚠️ pgvector may become a bottleneck at very large scale → migration path to Qdrant or a
  read-replica-dedicated vector store (future ADR).

---

## ADR-007: Celery + Redis with dedicated queues

**Status:** Accepted · **Date:** 2026-06-15

### Context
Ingestion (minutes, I/O-bound), embedding (rate-limited), LLM scoring (cost-bound), and
email (fast) have very different profiles. A single queue lets slow work starve fast work.

### Decision
Celery on Redis with **dedicated queues**: `ingestion`, `embedding`, `matching`, `notify`,
`default`. Celery Beat for the nightly pipeline. Idempotent tasks (dedup hash / upsert),
exponential backoff + jitter retries, dead-letter handling, per-source and per-provider
rate limits via Redis token buckets. High concurrency for I/O queues, low for `matching`.

### Consequences
- ✅ Workload isolation; independent scaling per queue.
- ✅ Safe retries (idempotency) and provider-quota protection.
- ⚠️ More worker configuration; Flower added for queue observability.

---

## ADR-008: Plugin-based ingestion adapters

**Status:** Accepted · **Date:** 2026-06-15

### Context
Job sources are heterogeneous (APIs, feeds, scrapers) and we'll add many over time. A
broken source must never break the pipeline.

### Decision
Each source is a self-contained adapter in `integrations/sources/` implementing a common
interface (`fetch() → list[RawPosting]`). A normalization layer maps source fields into the
canonical schema. Per-source circuit breaker disables a failing source after N consecutive
failures and alerts. **Prefer official APIs/feeds; scrape only where ToS and robots.txt permit.**

### Consequences
- ✅ Adding a source is a new file, not a rewrite; sources are independently testable.
- ✅ Pipeline resilience via per-source isolation + circuit breaking.
- ⚠️ Scrapers are fragile and carry legal constraints — gated behind compliance review.

---

## ADR-009: Authentication — JWT access + rotating refresh tokens

**Status:** Accepted · **Date:** 2026-06-15

### Context
CVs are PII; auth must be robust. We need stateless API auth plus secure session longevity.

### Decision
Short-lived JWT access tokens (~15 min) + rotating refresh tokens stored in `httpOnly`,
`secure` cookies, with refresh-token-reuse detection. Argon2id password hashing.
Email verification and password reset via single-use, expiring tokens. Every data query is
scoped by `user_id` server-side; row ownership enforced in repositories.

### Consequences
- ✅ Stateless, horizontally scalable API; strong session security.
- ✅ Reuse detection mitigates stolen-refresh-token attacks.
- ⚠️ Cookie auth requires CSRF protection and a strict CORS allowlist.

---

## ADR-010: AWS on ECS Fargate, provisioned with Terraform

**Status:** Accepted · **Date:** 2026-06-15

### Context
We want production-grade, reproducible infrastructure that demonstrates DevOps skill
without the operational weight of Kubernetes at MVP stage.

### Decision
AWS provisioned entirely via Terraform (`infra/terraform/`). Compute on **ECS Fargate**
(API service + worker services). RDS PostgreSQL (encrypted), ElastiCache Redis, S3 (CVs,
SSE-KMS), SES (email), Secrets Manager (secrets), CloudWatch + OpenTelemetry (observability).
DB/Redis in private subnets; least-privilege IAM; security groups locked down.

### Consequences
- ✅ Reproducible, reviewable infra; no manual console drift.
- ✅ Fargate autoscaling on queue depth without managing nodes.
- ⚠️ Migration path to EKS documented for when orchestration needs grow (future ADR).

---

## Appendix: ADR template

```markdown
## ADR-XXX: <short title>

**Status:** Proposed · **Date:** YYYY-MM-DD

### Context
What forces are at play? What problem are we solving?

### Decision
What we decided to do.

### Consequences
- ✅ Positive outcomes
- ⚠️ Trade-offs / risks / follow-ups
```
