# JobHunter AI — developer task runner.
# Most gates are delegated to scripts/preflight.sh so local runs and the
# git pre-commit hook stay identical.

.DEFAULT_GOAL := help
.PHONY: help setup check fix lint fmt test api-check web-check hooks \
	up down restart logs ps

# Local dev stack (Postgres + Redis). Reads variables from the repo-root .env.
COMPOSE := docker compose --env-file .env -f infra/compose/docker-compose.yml

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install dev dependencies for each app that exists
	@if [ -d apps/api ]; then \
		echo ">> apps/api"; \
		if command -v uv >/dev/null 2>&1; then (cd apps/api && uv sync); \
		else echo "   uv not found — see https://docs.astral.sh/uv/"; fi; \
	fi
	@if [ -f apps/web/package.json ]; then \
		echo ">> apps/web"; (cd apps/web && npm install); \
	fi

check: ## Run all quality gates (lint, format check, type-check, tests)
	@scripts/preflight.sh

fix: ## Autofix formatting/lint, then re-check
	@scripts/preflight.sh --fix

api-check: ## Run backend gates only
	@scripts/preflight.sh --api-only

web-check: ## Run frontend gates only
	@scripts/preflight.sh --web-only

test: ## Run tests only (skip lint/type gates)
	@scripts/preflight.sh

hooks: ## (Re)install the pre-commit hook into .git/hooks
	@ln -sf ../../scripts/preflight.sh .git/hooks/pre-commit 2>/dev/null \
		|| cp scripts/preflight.sh .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "pre-commit hook installed."

up: ## Start the local dev stack (Postgres + Redis) in the background
	@test -f .env || (echo "No .env found — run: cp .env.example .env" && exit 1)
	@$(COMPOSE) up -d
	@echo "Stack up. Check health with 'make ps'."

down: ## Stop the local dev stack (keeps data volumes)
	@$(COMPOSE) down

restart: ## Restart the local dev stack
	@$(COMPOSE) down && $(COMPOSE) up -d

logs: ## Tail logs from the local dev stack
	@$(COMPOSE) logs -f

ps: ## Show status/health of the local dev stack
	@$(COMPOSE) ps
