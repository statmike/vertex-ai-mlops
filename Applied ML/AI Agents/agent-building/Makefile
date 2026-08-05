.PHONY: help install setup cleanup run discovery test lint format check \
        deploy-discovery deploy-concierge deploy-info deploy-delete \
        eval-local eval-platform observe

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies (uv)
	uv sync --extra dev

setup: ## Provision cloud resources (run once; skip if you have your own data)
	uv run python scripts/setup.py

cleanup: ## Tear down everything setup.py created
	uv run python scripts/cleanup.py

discovery: ## Serve the discovery agent over A2A (run in its own terminal)
	@host=$$(uv run python -c "from config import DISCOVERY_A2A_HOST; print(DISCOVERY_A2A_HOST)"); \
	port=$$(uv run python -c "from config import DISCOVERY_A2A_PORT; print(DISCOVERY_A2A_PORT)"); \
	echo "Serving discovery on $$host:$$port (from config.py)"; \
	uv run uvicorn agent_discovery.agent:a2a_app --host $$host --port $$port

run: ## Launch the concierge in the ADK web UI (needs `make discovery` running)
	uv run adk web .

test: ## Run all tests
	uv run pytest

lint: ## Run linter + format check (matches CI; no files changed)
	uv run ruff check .
	uv run ruff format --check .

format: ## Auto-format code (ruff format + import sorting)
	uv run ruff format .
	uv run ruff check --fix --select I .

check: lint test ## Run lint (check + format) then tests

deploy-discovery: ## Deploy the discovery agent to Agent Runtime (deploy this first)
	uv run python deploy/deploy.py discovery

deploy-concierge: ## Deploy the concierge to Agent Runtime (set DISCOVERY_A2A_URL first)
	uv run python deploy/deploy.py concierge

deploy-info: ## Show deployment info for both agents
	uv run python deploy/deploy.py discovery --info
	uv run python deploy/deploy.py concierge --info

deploy-delete: ## Tear down both Agent Runtime deployments
	uv run python deploy/deploy.py concierge --delete
	uv run python deploy/deploy.py discovery --delete

eval-local: ## Run the offline eval harness (run scenarios, then judge + report)
	uv run python optimize/run_local.py
	uv run python optimize/judge_local.py

eval-platform: ## Run the managed Simulation + Evaluation engine
	uv run python optimize/simulate_platform.py
	uv run python optimize/evaluate_platform.py

observe: ## Summarize the BigQuery agent event log (observability)
	uv run python optimize/observe_events.py
