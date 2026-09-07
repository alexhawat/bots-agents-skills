# Discogs-Bot (OpenClaw pack)

OpenClaw skill (ClawHub-style `SKILL.md` with YAML frontmatter) for the Discogs
session-replay bot. This pack is **instructions only** — the runnable scripts
(27 task slugs, stdlib-only Python, shared `_lib/`) live in
`grok_bots/discogs-bot/` in this repo and are referenced from a local clone,
never copied.

**Repo:** https://github.com/alexhawat/bots-agents-skills
**Path:** `openclaw/discogs-bot/`
**Canonical scripts:** `grok_bots/discogs-bot/`

## Requirements

- **Python 3.9+.** The automation scripts are **standard-library only**.
- [`uv`](https://docs.astral.sh/uv/) for the dev workflow (`make test`, `make lint`).
- Optional: `cryptography`, used *only* by the Chrome SQLite decrypt fallback in
  `export_cookies.py`.
- An OpenClaw agent with shell access.

## Install on OpenClaw

1. Clone the repo and point the env vars at it:

```bash
git clone https://github.com/alexhawat/bots-agents-skills.git ~/bots-agents-skills
export BOTS_REPO_ROOT=~/bots-agents-skills      # add to your shell profile
export DISCOGS_AUTH_DIR=~/.config/discogs-bot   # local jar, outside the clone
```

2. Reference this skill from your OpenClaw workspace config (point the
   workspace at `openclaw/discogs-bot/SKILL.md`), or install it clawhub-style
   by copying the folder into your workspace's skills directory.
3. Create the local auth dir from the example:

```bash
mkdir -p "$DISCOGS_AUTH_DIR"
cp "$BOTS_REPO_ROOT/grok_bots/discogs-bot/discogs-auth/personal.env.example" \
   "$DISCOGS_AUTH_DIR/personal.env"   # set USERNAME + CURRENCY
```

4. Sign in to Discogs in the runtime's browser (complete login/2FA
   interactively), then:

```bash
python3 "$BOTS_REPO_ROOT/grok_bots/discogs-bot/discogs-auth/export_cookies.py"
python3 "$BOTS_REPO_ROOT/grok_bots/discogs-bot/discogs-scripts/auth-refresh/scripts/refresh.py" --check-only
```

Expect `ok viewer=…`.

## Verify (offline, no account)

```bash
cd "$BOTS_REPO_ROOT/grok_bots/discogs-bot"
make test    # unit tests over the pure parsers
make smoke   # replay the redacted HAR fixture + har-diff
make check   # lint + test
```

## Mutation safety

Anything that changes state is dry-run by default and exits **2**; pass
`--confirm` to execute. Cart add needs `--confirm` **and**
`--i-really-mean-it`. Checkout and payment stay a human browser step.

## Never commit / never ship

Live `auth.env`, `personal.env`, `chrome-cookie-seed.json`, unredacted HARs, or
Cookie values. The jar stays in `$DISCOGS_AUTH_DIR` at mode 0600 — never inside
the clone. Scripts never print Cookie values, and error text never carries
request headers.

## Source of truth

The scripts live in `grok_bots/discogs-bot/` on the main branch of
alexhawat/bots-agents-skills. This pack is instructions only. Run
`git -C "$BOTS_REPO_ROOT" pull` to update.
