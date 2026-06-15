#!/usr/bin/env bash
#
# preflight.sh — run all quality gates before committing / opening a PR.
#
# Runs, for whichever apps exist in the monorepo:
#   Backend (apps/api):  ruff format check · ruff lint · mypy · pytest
#   Frontend (apps/web): prettier check · eslint · tsc · tests
#
# Design notes:
#   * Gracefully SKIPs a stack/tool that isn't present yet (the repo grows PR by PR).
#   * Runs every gate and reports a summary at the end (does NOT fail-fast), so you
#     see all problems in one pass.
#   * `--fix` runs the formatters/autofixers in write mode first, then re-checks.
#   * Honors a focused scope via --api-only / --web-only.
#
# Usage:
#   scripts/preflight.sh            # check everything that exists
#   scripts/preflight.sh --fix      # autofix formatting/lint, then check
#   scripts/preflight.sh --api-only
#   scripts/preflight.sh --web-only
#   scripts/preflight.sh --no-tests # skip the (slower) test gates
#
# Exit code: 0 if every executed gate passed, 1 if any failed.

set -uo pipefail

# --- locate repo root (this script lives in <root>/scripts) -------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"

# --- options ------------------------------------------------------------------
FIX=0
RUN_API=1
RUN_WEB=1
RUN_TESTS=1

for arg in "$@"; do
  case "$arg" in
    --fix)       FIX=1 ;;
    --api-only)  RUN_WEB=0 ;;
    --web-only)  RUN_API=0 ;;
    --no-tests)  RUN_TESTS=0 ;;
    -h|--help)
      sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "Unknown option: $arg (try --help)" >&2
      exit 2 ;;
  esac
done

# --- pretty output ------------------------------------------------------------
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; BLUE=$'\033[34m'; RESET=$'\033[0m'
else
  BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; BLUE=""; RESET=""
fi

PASSED=(); FAILED=(); SKIPPED=()

header() { printf '\n%s━━ %s %s\n' "$BOLD$BLUE" "$1" "$RESET"; }
have()   { command -v "$1" >/dev/null 2>&1; }

# run_gate <label> <command...> — executes a gate inside the current shell dir.
run_gate() {
  local label="$1"; shift
  printf '%s▶ %s%s\n' "$DIM" "$label" "$RESET"
  if "$@"; then
    printf '%s  ✔ %s%s\n' "$GREEN" "$label" "$RESET"
    PASSED+=("$label")
  else
    printf '%s  ✗ %s FAILED%s\n' "$RED" "$label" "$RESET"
    FAILED+=("$label")
  fi
}

skip() {
  printf '%s  ⤼ %s (skipped — %s)%s\n' "$YELLOW" "$1" "$2" "$RESET"
  SKIPPED+=("$1")
}

# =============================================================================
# Backend: apps/api  (Python — ruff / mypy / pytest)
# =============================================================================
check_api() {
  header "Backend · apps/api"

  if [ ! -d "$API_DIR" ]; then
    skip "backend" "apps/api does not exist yet"
    return
  fi

  # Prefer `uv run` if the project uses uv, else fall back to tools on PATH.
  local RUN=()
  if have uv && [ -f "$API_DIR/pyproject.toml" ]; then
    RUN=(uv run --project "$API_DIR")
  fi

  pushd "$API_DIR" >/dev/null

  # ruff — formatter
  if have ruff || [ "${#RUN[@]}" -gt 0 ]; then
    if [ "$FIX" -eq 1 ]; then
      run_gate "ruff format (write)" "${RUN[@]}" ruff format .
      run_gate "ruff lint --fix"     "${RUN[@]}" ruff check --fix .
    fi
    run_gate "ruff format (check)" "${RUN[@]}" ruff format --check .
    run_gate "ruff lint"           "${RUN[@]}" ruff check .
  else
    skip "ruff" "ruff not installed"
  fi

  # mypy — type checking (only if configured)
  if grep -qs "mypy" pyproject.toml setup.cfg mypy.ini 2>/dev/null; then
    if have mypy || [ "${#RUN[@]}" -gt 0 ]; then
      run_gate "mypy" "${RUN[@]}" mypy .
    else
      skip "mypy" "mypy not installed"
    fi
  else
    skip "mypy" "no mypy config found"
  fi

  # pytest — tests
  if [ "$RUN_TESTS" -eq 1 ]; then
    if have pytest || [ "${#RUN[@]}" -gt 0 ]; then
      run_gate "pytest" "${RUN[@]}" pytest -q
    else
      skip "pytest" "pytest not installed"
    fi
  else
    skip "pytest" "--no-tests"
  fi

  popd >/dev/null
}

# =============================================================================
# Frontend: apps/web  (TypeScript — prettier / eslint / tsc / tests)
# =============================================================================
check_web() {
  header "Frontend · apps/web"

  if [ ! -d "$WEB_DIR" ]; then
    skip "frontend" "apps/web does not exist yet"
    return
  fi
  if [ ! -f "$WEB_DIR/package.json" ]; then
    skip "frontend" "apps/web has no package.json yet"
    return
  fi

  # Detect package manager from the lockfile.
  local PM=""
  if   [ -f "$WEB_DIR/pnpm-lock.yaml" ]; then PM="pnpm"
  elif [ -f "$WEB_DIR/yarn.lock" ];      then PM="yarn"
  elif [ -f "$WEB_DIR/package-lock.json" ]; then PM="npm"
  elif have npm; then PM="npm"
  fi

  if [ -z "$PM" ] || ! have "$PM"; then
    skip "frontend" "no usable package manager (pnpm/yarn/npm) found"
    return
  fi

  pushd "$WEB_DIR" >/dev/null

  # helper: does package.json declare this script?
  has_script() { node -e "process.exit(require('./package.json').scripts?.['$1']?0:1)" 2>/dev/null; }
  # run an npm script across pnpm/yarn/npm
  pm_run() { case "$PM" in npm) npm run "$@";; *) "$PM" "$@";; esac; }

  if [ ! -d node_modules ]; then
    skip "frontend gates" "node_modules missing — run '$PM install' first"
    popd >/dev/null
    return
  fi

  # prettier — formatter
  if has_script format && [ "$FIX" -eq 1 ]; then
    run_gate "prettier (write)" pm_run format
  fi
  if has_script format:check; then
    run_gate "prettier (check)" pm_run format:check
  elif have npx; then
    run_gate "prettier (check)" npx prettier --check .
  else
    skip "prettier" "no format:check script and npx unavailable"
  fi

  # eslint — linter
  if has_script lint; then
    if [ "$FIX" -eq 1 ] && has_script "lint:fix"; then
      run_gate "eslint --fix" pm_run "lint:fix"
    fi
    run_gate "eslint" pm_run lint
  else
    skip "eslint" "no lint script in package.json"
  fi

  # tsc — type checking
  if has_script typecheck; then
    run_gate "tsc" pm_run typecheck
  elif have npx && [ -f tsconfig.json ]; then
    run_gate "tsc --noEmit" npx tsc --noEmit
  else
    skip "tsc" "no typecheck script / tsconfig"
  fi

  # tests
  if [ "$RUN_TESTS" -eq 1 ]; then
    if has_script test; then
      run_gate "frontend tests" pm_run test
    else
      skip "frontend tests" "no test script in package.json"
    fi
  else
    skip "frontend tests" "--no-tests"
  fi

  popd >/dev/null
}

# =============================================================================
# Run
# =============================================================================
printf '%sPreflight — quality gates%s  %s(root: %s)%s\n' \
  "$BOLD" "$RESET" "$DIM" "$ROOT_DIR" "$RESET"
[ "$FIX" -eq 1 ] && printf '%smode: --fix (autofix then check)%s\n' "$YELLOW" "$RESET"

[ "$RUN_API" -eq 1 ] && check_api
[ "$RUN_WEB" -eq 1 ] && check_web

# --- summary ------------------------------------------------------------------
header "Summary"
printf '%s  passed:  %d%s\n' "$GREEN" "${#PASSED[@]}" "$RESET"
printf '%s  skipped: %d%s\n' "$YELLOW" "${#SKIPPED[@]}" "$RESET"
printf '%s  failed:  %d%s\n' "$RED" "${#FAILED[@]}" "$RESET"

if [ "${#FAILED[@]}" -gt 0 ]; then
  printf '\n%s✗ Preflight failed:%s\n' "$RED$BOLD" "$RESET"
  for f in "${FAILED[@]}"; do printf '    - %s\n' "$f"; done
  exit 1
fi

if [ "${#PASSED[@]}" -eq 0 ]; then
  printf '\n%s⚠ Nothing to check yet — no gates ran.%s\n' "$YELLOW" "$RESET"
  exit 0
fi

printf '\n%s✓ All gates passed — good to commit.%s\n' "$GREEN$BOLD" "$RESET"
exit 0
