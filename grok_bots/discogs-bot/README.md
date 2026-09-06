# Discogs-Bot (public pack)

Automates Discogs from a signed-in session: capture the network traffic for a task
once, then replay the API directly instead of driving the UI. 27 task scripts over a
shared `_lib/`, plus the cookie-export helpers that keep the session alive.

**Repo:** https://github.com/alexhawat/bots-agents-skills
**Path:** `grok_bots/discogs-bot/`
**License:** MIT (see `LICENSE`)

## Requirements

- **Python 3.9+.** The automation scripts are **standard-library only**.
- [`uv`](https://docs.astral.sh/uv/) for the dev workflow (`make test`, `make lint`).
- Optional: `cryptography`, used *only* by the Chrome SQLite decrypt fallback in
  `export_cookies.py`. The preferred CDP and seed paths do not need it.

## Try it without an account

The offline paths need no cookie, no network, and no Discogs account:

```bash
make install   # uv sync --group dev
make test      # 96 unit tests over the pure parsers
make smoke     # replay the redacted HAR fixture + run har-diff
make check     # lint + test; run this before committing
```

`make help` lists every target.

## Where auth lives

Scripts read a Cookie jar plus non-secret personal overrides. Paths default to the
Grok Bot box layout but **every one is environment overridable**, so a plain clone
works without `/home/box` or `/workspace` existing:

| Variable | Default | Holds |
|---|---|---|
| `DISCOGS_AUTH_DIR` | `/home/box/discogs-auth` | directory for both files below |
| `DISCOGS_AUTH_ENV` | `$DISCOGS_AUTH_DIR/auth.env` | `COOKIE=`, `USER_AGENT=` (mode 0600) |
| `DISCOGS_PERSONAL_ENV` | `$DISCOGS_AUTH_DIR/personal.env` | `USERNAME`, `CURRENCY` |
| `DISCOGS_WORK_AUTH` | `/workspace/discogs-scripts/_auth` | pointer dir (`AUTH_PATH.txt`) |
| `DISCOGS_COOKIE_SEED` | box seed path | Chrome cookie seed, exporter only |

The loader (`_lib/auth.py`) and **both** exporters — `export_cookies.py` and the
CDP helper `export_from_display.mjs` — resolve these the same way, per call, so
they cannot disagree about where the jar lives.

```bash
export DISCOGS_AUTH_DIR=~/.config/discogs-bot
mkdir -p "$DISCOGS_AUTH_DIR"
cp discogs-auth/personal.env.example "$DISCOGS_AUTH_DIR/personal.env"   # set USERNAME + CURRENCY
# then put COOKIE=... into "$DISCOGS_AUTH_DIR/auth.env" (see below)
uv run python discogs-scripts/auth-refresh/scripts/refresh.py --check-only   # expect: ok viewer=…
```

Merge order, later wins: shared `auth.env` → `personal.env` → task-local `auth.env`
→ explicit `--auth` override.

## Install on a Grok Bot box

1. Import the Discogs-Bot **public template** in Grok Bot (persona + skill).
2. Copy this folder onto the box:

```bash
# from a clone of alexhawat/bots-agents-skills
cp -a grok_bots/discogs-bot/discogs-scripts/. /workspace/discogs-scripts/
cp -a grok_bots/discogs-bot/discogs-auth/. /home/box/discogs-auth/
```

3. Sign in to Discogs in **that** bot's Chrome (`request_box_help` for login/2FA).
4. `python3 /home/box/discogs-auth/export_cookies.py`
5. `python3 /workspace/discogs-scripts/auth-refresh/scripts/refresh.py --check-only`
6. Copy `discogs-auth/personal.env.example` → `/home/box/discogs-auth/personal.env`
   and set `USERNAME` + `CURRENCY`.

## Never commit / never ship

Live `auth.env`, `personal.env`, `chrome-cookie-seed.json`, unredacted HARs, or Cookie
values. The root `.gitignore` blocks all of these, and `*.har` is denied by default —
the three committed fixtures are redacted and were added deliberately.

Scripts never print Cookie values, and error text never carries request headers.
The exporters write the jar once, at mode 0600, and put only a **path pointer**
(`AUTH_PATH.txt`) under the work tree — the secret is never duplicated into a
checkout.

CI enforces the last part: `.github/workflows/discogs-bot.yml` fails the build if a
live `auth.env`/`personal.env` is committed, or if any committed HAR still carries a
`Cookie`/`Authorization` value.

## Mutation safety

Anything that changes state is dry-run by default: it prints the planned mutation and
exits **2**. Pass `--confirm` to execute. Adding to the cart needs `--confirm` **and**
`--i-really-mean-it`. Checkout and payment stay a human browser step.

## Layout

- `PERSONA.md` — storefront + scrubbed charter (for humans / template authors)
- `docs/` — capture→script skill, `EXPORT.md`, `MANUAL-SMOKE-TESTS.md` (live-session checks)
- `discogs-scripts/` — automation tree: `_lib/` + 27 task folders
- `discogs-auth/` — cookie export helpers + `*.example` env files
- `tests/` — offline unit tests (`make test`)

Each task folder is `<slug>/{scripts,capture,README.md}`: the script, the redacted
capture that documents its endpoints, and how to run it.

## Adding a task

1. Capture the traffic once (HAR or copy-as-cURL); redact cookies before saving.
2. Create `discogs-scripts/<slug>/{scripts,capture}` + a README with the endpoint table.
3. Put shared logic in `_lib/`; raise `_lib.errors.DiscogsError` subclasses, never
   `SystemExit` — scripts turn those into exit codes via `cli_main`.
4. Add tests for any new pure parser, then `make check`.
5. Update the Live table in `docs/discogs-capture-to-script.SKILL.md`.
