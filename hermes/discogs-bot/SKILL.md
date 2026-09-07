# Discogs-Bot (Hermes skill)

Automates Discogs from a signed-in session. The runnable scripts are **not** in
this skill folder — they live in a clone of the `alexhawat/bots-agents-skills`
repository. This skill tells you where the clone is and how to run it.

## Locate the repo clone

Scripts run from the repo root, referenced by the `BOTS_REPO_ROOT` env var
(default `~/bots-agents-skills`):

```bash
export BOTS_REPO_ROOT="${BOTS_REPO_ROOT:-$HOME/bots-agents-skills}"
git -C "$BOTS_REPO_ROOT" pull   # refresh before relying on recent changes
```

If the clone is missing, create it:

```bash
git clone https://github.com/alexhawat/bots-agents-skills.git "$BOTS_REPO_ROOT"
```

All script paths below are relative to `$BOTS_REPO_ROOT/grok_bots/discogs-bot/`.
Never copy scripts out of the clone; run them in place so `git pull` keeps them
current.

## Auth setup

Every auth path is env-overridable. Point the loader at a local jar (never
inside the repo clone):

```bash
export DISCOGS_AUTH_DIR=~/.config/discogs-bot
mkdir -p "$DISCOGS_AUTH_DIR"
cp "$BOTS_REPO_ROOT/grok_bots/discogs-bot/discogs-auth/personal.env.example" \
   "$DISCOGS_AUTH_DIR/personal.env"   # set USERNAME + CURRENCY
```

`auth.env` (`COOKIE=`, `USER_AGENT=`, mode 0600) goes in the same directory.
Optional overrides: `DISCOGS_AUTH_ENV`, `DISCOGS_PERSONAL_ENV`,
`DISCOGS_WORK_AUTH`, `DISCOGS_COOKIE_SEED`. Merge order, later wins: shared
`auth.env` → `personal.env` → task-local `auth.env` → explicit `--auth`.

First run or dead session: ask the user to complete login/2FA interactively in
the runtime's browser, then refresh the jar:

```bash
python3 "$BOTS_REPO_ROOT/grok_bots/discogs-bot/discogs-auth/export_cookies.py"
python3 "$BOTS_REPO_ROOT/grok_bots/discogs-bot/discogs-scripts/auth-refresh/scripts/refresh.py" --check-only
```

Expect `ok viewer=…`. Prefer `auth-refresh` (`--check-only`, then
refresh/export) before failing tasks on `viewer=null`.

## Running tasks

27 task slugs live under `discogs-scripts/<slug>/scripts/`, over a shared
`_lib/`. Examples (run from anywhere — paths are absolute via `$BOTS_REPO_ROOT`):

```bash
cd "$BOTS_REPO_ROOT/grok_bots/discogs-bot"
python3 discogs-scripts/collection-search/scripts/search_collection.py 'Domingo Federico'
python3 discogs-scripts/wantlist-search/scripts/search_wantlist.py --query "blue note"
python3 discogs-scripts/orders-list/scripts/list_orders.py
```

Each slug folder has its own README with the endpoint table and flags.

## Safety rules

- Anything that changes state is **dry-run by default**: it prints the planned
  mutation and exits 2. Pass `--confirm` to execute.
- Adding to the cart needs `--confirm` **and** `--i-really-mean-it`.
- Checkout and payment stay a human browser step.
- Never print Cookie values or request headers. Never paste secrets into chat.
- No inventing endpoints or collection state.

## Offline verification

No account needed:

```bash
cd "$BOTS_REPO_ROOT/grok_bots/discogs-bot"
make test    # unit tests over the pure parsers
make smoke   # replay the redacted HAR fixture + har-diff
make check   # lint + test
```
