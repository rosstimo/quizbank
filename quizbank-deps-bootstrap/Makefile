# Make the gods of reproducibility slightly less angry.
SHELL := /usr/bin/env bash
.ONESHELL:
.DEFAULT_GOAL := help

VENV := .venv
UV := uv

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONWARNINGS=ignore

help:  ## Show targets
	@grep -E '^[a-zA-Z0-9_-]+:\s.*##' Makefile | sed 's/:.*##/: /' | column -t -s ':'

setup: ## Bootstrap dev env (uv, venv, hooks)
	command -v $(UV) >/dev/null || (echo "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	$(UV) sync
	pre-commit install

sync: ## Sync deps from pyproject + uv.lock
	$(UV) sync

lock: ## Resolve and lock exact versions
	$(UV) lock

add-%: ## Add a runtime dependency, e.g., `make add-pyyaml`
	$(UV) add $(patsubst add-%,%,$@)

add-dev-%: ## Add a dev dependency, e.g., `make add-dev-pytest`
	$(UV) add --dev $(patsubst add-dev-%,%,$@)

fmt: ## Format code
	pre-commit run black --all-files
	pre-commit run prettier --all-files || true

lint: ## Lint (ruff, yamllint, codespell)
	pre-commit run ruff --all-files
	pre-commit run yamllint --all-files || true
	pre-commit run codespell --all-files || true

typecheck: ## mypy type checking
	mypy . || true

check: lint typecheck ## Run all checks

# Placeholder build steps. Wire these to your actual generators.
build: ## Build artifacts (QTI/Typst/etc.). Edit as needed.
	@mkdir -p outputs
	echo "Pretending to build quizzes into outputs/ ..."

clean: ## Clean caches and outputs
	rm -rf .pytest_cache .mypy_cache .ruff_cache outputs artifacts

ci: ## CI entrypoint: install locked deps and run checks
	$(UV) sync --frozen
	make check
