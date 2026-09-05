# Discogs-Bot export surface

## Include in a shareable template
- Scrubbed persona (Discogs-Bot) — no owner name, username, or location
- Skill: `discogs-capture-to-script` (procedure + Live inventory)
- Script tree under `discogs-scripts/<slug>/` (code, README procedure, redacted fixtures)
- This file (`docs/EXPORT.md`)
- `_lib/` helpers, `tests/`, `Makefile`, `pyproject.toml`, `LICENSE`
- Auth helpers under `/home/box/discogs-auth/` that are **procedure-only**: `export_cookies.py`, `export_from_display.mjs`, `README.md` (no secrets)

## Never include
- `/home/box/discogs-auth/auth.env` (Cookie jar)
- `/home/box/discogs-auth/personal.env` (USERNAME, CURRENCY, …)
- Any task-local `auth.env`
- Cookie / Authorization values in chat, README samples, or HAR dumps that still contain secrets (redact first)
- Live cookie seed files (`chrome-cookie-seed.json`)

## Auth after import
1. Recipient signs in with **their** Discogs-Bot Chrome (`browserUse` / `request_box_help` for login).
2. Auto-import: `python3 /home/box/discogs-auth/export_cookies.py`
   - Prefers live CDP from **this** Chrome (`export_from_display.mjs`), then shared seed, then SQLite decrypt.
3. Confirm: `python3 auth-refresh/scripts/refresh.py --check-only` → `ok viewer=…`
4. Set their `personal.env` (`USERNAME`, `CURRENCY`) — never put those in the persona.
5. Off-box clones: set `DISCOGS_AUTH_DIR` instead of creating `/home/box` (see root README).

## Verify an import without an account

`make test` and `make smoke` run fully offline — no cookie, no network. Run both
before trusting a freshly copied pack.
