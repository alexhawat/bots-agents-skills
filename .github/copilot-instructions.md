# Copilot instructions — bots-agents-skills

Reusable building blocks for agentic workflows: bot packs, agent configs, and
portable skills.

## Layout

- `grok_bots/` — canonical bot script packs (single source of truth for all
  runnable code). `discogs-bot/` (Python 3.9+, stdlib-only, uv + pytest + ruff,
  `make check` before committing) and `whatsapp-bot/` (Python 3.10+, Node 20+
  for headless CDP helpers).
- `hermes/`, `openclaw/` — instruction-only packs (persona + skill markdown) for
  those runtimes. They reference `grok_bots/` code via relative paths and env
  overrides; they must NEVER contain `.py`/`.mjs` files
  (`tools/pack_drift_guard.py` enforces this in CI).
- `tools/` — repo-level guards (`pack_drift_guard.py`).

## Hard rules

- Never commit secrets: live `auth.env` / `personal.env`, cookies, unredacted
  HARs, chat transcripts, phone numbers. Committed fixtures stay redacted.
- Library code raises typed errors (`_lib/errors.py`), never `SystemExit`;
  scripts map errors to exit codes exactly once, via `cli_main`.
- Mutating scripts are dry-run by default and require `--confirm`.
- Never invent private API endpoints (Discogs: replay captured traffic only;
  WhatsApp: WebSocket/protobuf is opaque — use headless CDP or browser mode).
- Runtime code is standard-library only; dev tooling (pytest, ruff) lives in
  the uv `dev` dependency group of each pack.

## Working in this tree

- discogs-bot: `cd grok_bots/discogs-bot && make check` (ruff + pytest + smoke).
- whatsapp-bot: `cd grok_bots/whatsapp-bot && make check`.
- Repo-level: `make install-hooks` installs the pre-push trusted-authors guard
  (`.github/trusted-authors.txt` via `scripts/check_push_authors.py`).
