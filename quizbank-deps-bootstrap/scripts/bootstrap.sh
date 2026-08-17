#!/usr/bin/env bash
set -euo pipefail

echo "==> Running system dependency check"
./scripts/check_system_deps.sh || { echo "Install missing deps and retry."; exit 1; }

echo "==> Bootstrapping Python env with uv"
if ! command -v uv >/dev/null; then
  echo "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

uv sync

echo "==> Installing pre-commit hooks"
pre-commit install

echo "==> Done. Activate env with: source .venv/bin/activate (uv can auto-activate in some shells)"
