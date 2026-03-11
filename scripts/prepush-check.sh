#!/usr/bin/env bash
set -euo pipefail

SKIP_BACKEND_TESTS=false
SKIP_FRONTEND_BUILD=false

for arg in "$@"; do
  case "$arg" in
    --skip-backend-tests)
      SKIP_BACKEND_TESTS=true
      ;;
    --skip-frontend-build)
      SKIP_FRONTEND_BUILD=true
      ;;
    *)
      echo "[prepush] Unknown option: $arg"
      echo "Usage: ./scripts/prepush-check.sh [--skip-backend-tests] [--skip-frontend-build]"
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "[prepush] Starting pre-push validation..."

if [ "$SKIP_BACKEND_TESTS" = false ]; then
  echo "[prepush] Running backend test suite in Docker..."
  docker compose exec backend pytest -q
  echo "[prepush] Backend tests passed."
else
  echo "[prepush] Skipping backend tests."
fi

if [ "$SKIP_FRONTEND_BUILD" = false ]; then
  echo "[prepush] Running frontend production build..."
  (
    cd "$REPO_ROOT/frontend"
    npm run build
  )
  echo "[prepush] Frontend build passed."
else
  echo "[prepush] Skipping frontend build."
fi

echo "[prepush] All checks passed. Safe to push."
