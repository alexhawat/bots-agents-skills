# WhatsApp-Bot — dev tasks. Everything runs through uv.
#   https://docs.astral.sh/uv/
.DEFAULT_GOAL := help
.PHONY: help install test lint fmt check smoke clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Sync the dev environment (creates .venv)
	uv sync --group dev

test: ## Run the unit tests (offline, no auth needed)
	uv run pytest

lint: ## Lint without modifying files
	uv run ruff check .

fmt: ## Auto-fix lint and format
	uv run ruff check --fix .
	uv run ruff format .

check: lint test ## Lint + test — run this before committing

smoke: ## Offline smoke test: har-diff against its fixture, no network or auth
	uv run python har-diff/scripts/diff.py har-diff/fixtures/sample-urls.txt

clean: ## Remove caches and build artifacts
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
