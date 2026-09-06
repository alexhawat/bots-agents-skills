# Discogs-Bot — dev tasks. Everything runs through uv.
#   https://docs.astral.sh/uv/
.DEFAULT_GOAL := help
.PHONY: help install test lint fmt check auth-check smoke har-guard clean

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

auth-check: ## Verify the session jar is alive (needs a real cookie)
	uv run python discogs-scripts/auth-refresh/scripts/refresh.py --check-only

smoke: ## Offline smoke test: replay the redacted HAR, no network or auth
	uv run python discogs-scripts/collection-search/scripts/search_collection.py 'Domingo Federico' \
		--from-har discogs-scripts/collection-search/capture/collection-federico.har
	uv run python discogs-scripts/har-diff/scripts/diff.py \
		discogs-scripts/har-diff/fixtures/sample-curls.txt

clean: ## Remove caches and build artifacts
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache

har-guard: ## Check committed HARs carry no live session material (same check as CI)
	@root=$$(git rev-parse --show-toplevel); \
	  git -C $$root ls-files '*.har' | sed "s|^|$$root/|" \
	  | xargs -r uv run python tools/har_guard.py
