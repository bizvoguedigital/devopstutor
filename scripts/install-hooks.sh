#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

git config core.hooksPath .githooks
chmod +x .githooks/pre-push scripts/prepush-check.sh scripts/install-hooks.sh

echo "[hooks] Installed repo hooks."
echo "[hooks] core.hooksPath=$(git config core.hooksPath)"
