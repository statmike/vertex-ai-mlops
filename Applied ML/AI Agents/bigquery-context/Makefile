.PHONY: help install setup cleanup test lint format check clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies
	uv sync --extra dev

kernel: ## Register Jupyter kernel for this project's venv
	uv run python -m ipykernel install --user --name "bigquery-context" --display-name "Python (bigquery-context)"

setup: ## Create BQ datasets, views, and Dataplex profile scans
	uv run python scripts/setup.py

cleanup: ## Delete all BQ datasets and Dataplex scans created by setup
	uv run python scripts/cleanup.py

test: ## Run all tests
	uv run pytest

lint: ## Run linter (ruff check)
	uv run ruff check .

format: ## Auto-format code (ruff format + import sorting)
	uv run ruff format .
	uv run ruff check --fix --select I .

check: lint test ## Run lint then tests

clean: ## Remove build artifacts and caches
	rm -rf .venv .ruff_cache .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
