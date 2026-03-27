.PHONY: help install test test-unit test-cov lint format check clean cleanup cleanup-dry-run deploy undeploy deploy-info run

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies
	uv sync --extra dev

test: ## Run all tests
	uv run pytest

test-unit: ## Run unit tests only
	uv run pytest -k unit -v

test-cov: ## Run tests with HTML coverage report
	uv run pytest --cov-report=html

lint: ## Run linter (ruff check)
	uv run ruff check .

format: ## Auto-format code (ruff format + import sorting)
	uv run ruff format .
	uv run ruff check --fix --select I .

check: lint test ## Run lint then tests

clean: ## Remove build artifacts and caches
	rm -rf .venv .ruff_cache .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true

cleanup: ## Delete all cloud resources and local output (BQ, GCS, Agent Engine)
	uv run python scripts/cleanup.py --yes

cleanup-dry-run: ## Preview cleanup without deleting anything
	uv run python scripts/cleanup.py --dry-run

run: ## Launch adk web
	uv run adk web

deploy: ## Deploy agent to Vertex AI Agent Engine
	uv run python deploy/deploy.py

undeploy: ## Delete Agent Engine deployment
	uv run python deploy/deploy.py --delete

deploy-info: ## Show current deployment info
	uv run python deploy/deploy.py --info
