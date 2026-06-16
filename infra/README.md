# Infrastructure

| Dir          | Purpose                                                             | Introduced in   |
| ------------ | ------------------------------------------------------------------- | --------------- |
| `compose/`   | Local `docker-compose` stack (Postgres+pgvector, Redis, services)   | PR-002          |
| `docker/`    | Per-service Dockerfiles                                             | PR-002 / deploy |
| `terraform/` | AWS infrastructure as code (ECS Fargate, RDS, ElastiCache, S3, SES) | Phase 5         |

See [ADR-010](../docs/architecture/decisions.md#adr-010-aws-on-ecs-fargate-provisioned-with-terraform).
