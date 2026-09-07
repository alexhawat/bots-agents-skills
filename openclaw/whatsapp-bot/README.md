# WhatsApp-Bot (OpenClaw pack)

OpenClaw skill (ClawHub-style `SKILL.md` with YAML frontmatter) for the
WhatsApp Web bot. This pack is **instructions only** — the runnable scripts
(slug folders over a shared `_lib/`, headless CDP helpers) live in
`grok_bots/whatsapp-bot/` in this repo and are referenced from a local clone,
never copied.

**Repo:** https://github.com/alexhawat/bots-agents-skills
**Path:** `openclaw/whatsapp-bot/`
**Canonical scripts:** `grok_bots/whatsapp-bot/`

## Requirements

- **Python 3.10+** (stdlib preferred for task scripts)
- **Node 20+** for headless CDP helpers (`_lib/*.mjs`, `tools/capture_network.mjs`)
- A linked WhatsApp Web session (QR once; jar stays local)
- An OpenClaw agent with shell access

## Install on OpenClaw

1. Clone the repo and point the env var at it:

```bash
git clone https://github.com/alexhawat/bots-agents-skills.git ~/bots-agents-skills
export BOTS_REPO_ROOT=~/bots-agents-skills   # add to your shell profile
```

2. Reference this skill from your OpenClaw workspace config (point the
   workspace at `openclaw/whatsapp-bot/SKILL.md`), or install it clawhub-style
   by copying the folder into your workspace's skills directory.
3. Create a local auth dir and point the loaders at it:

```bash
mkdir -p ~/.config/whatsapp-auth
cd "$BOTS_REPO_ROOT/grok_bots/whatsapp-bot"
cp _auth/AUTH_PATH.txt.example _auth/AUTH_PATH.txt
cp _auth/PERSONAL_PATH.txt.example _auth/PERSONAL_PATH.txt
# edit the PATH files to point at ~/.config/whatsapp-auth
```

4. QR-link WhatsApp Web in the runtime's browser (scan interactively — see
   `docs/qr-link.md` in the grok pack), then export cookies into `auth.env`
   (mode 0600).

## Verify

```bash
cd "$BOTS_REPO_ROOT/grok_bots/whatsapp-bot"
python3 auth-check/scripts/check.py            # with probe
python3 auth-check/scripts/check.py --no-probe # offline: keys only
```

## Safety

- Mutating scripts require **`--confirm`**. Without it they dry-run.
- No mass messaging or spam tooling.
- Never invent WhatsApp private HTTP APIs — traffic is largely opaque
  (WebSocket / protobuf); use `--mode=headless` or `--mode=browser`.
- No secrets in git, chat, or logs.

## Never commit / never ship

Live `auth.env`, `personal.env`, cookies, localStorage dumps, chat transcripts,
media, phone numbers, or unredacted HARs. Only `_auth/*_PATH.txt.example`
ships; real path pointers stay gitignored. The jar lives in your local auth
dir at mode 0600 — never inside the clone.

## Source of truth

The scripts live in `grok_bots/whatsapp-bot/` on the main branch of
alexhawat/bots-agents-skills. This pack is instructions only. Run
`git -C "$BOTS_REPO_ROOT" pull` to update.
