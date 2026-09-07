.PHONY: install-hooks drift-guard persona-sync verify-discogs verify-whatsapp help

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install-hooks: ## Install git hooks (pre-push trusted-authors guard)
	git config core.hooksPath hooks
	chmod +x hooks/pre-push
	@echo "hooks installed (core.hooksPath=hooks)"

drift-guard: ## Fail if hermes/ or openclaw/ contain code files
	python3 tools/pack_drift_guard.py

persona-sync: ## Fail if a bot's persona versions disagree across infra
	python3 tools/persona_version_check.py

verify-discogs: ## Verify local Discogs install (add PROBE=1 for live auth probe)
	python3 tools/verify_install.py --bot discogs $(if $(PROBE),--probe,)

verify-whatsapp: ## Verify local WhatsApp install (add PROBE=1 for live auth probe)
	python3 tools/verify_install.py --bot whatsapp $(if $(PROBE),--probe,)
