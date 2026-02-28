.PHONY: help install test test-unit test-cov lint format check

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies
	uv sync --extra dev

test: ## Run all tests
	uv run pytest

test-unit: ## Run unit tests only
	uv run pytest agent_image_to_graph/tests/unit -v

test-cov: ## Run tests with HTML coverage report
	uv run pytest --cov-report=html

lint: ## Run linter (ruff check)
	uv run ruff check .

format: ## Auto-format code (ruff format + import sorting)
	uv run ruff format .
	uv run ruff check --fix --select I .

check: lint test ## Run lint then tests
