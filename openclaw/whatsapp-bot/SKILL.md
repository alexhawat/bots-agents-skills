---
name: whatsapp-bot
description: Automate WhatsApp Web for a linked account (list/read/search chats, send with confirm) via headless CDP scripts referenced from a clone of alexhawat/bots-agents-skills.
---

# WhatsApp-Bot (OpenClaw skill)

Session-backed automations for WhatsApp Web: link once with QR, then run
read/write scripts via headless CDP or browser UI automation. The runnable
scripts are **not** in this skill — they live in a clone of the
`alexhawat/bots-agents-skills` repository. You have shell access; run the
scripts in place from the clone.

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

All script paths below are relative to `$BOTS_REPO_ROOT/grok_bots/whatsapp-bot/`.
Never copy scripts out of the clone; run them in place so `git pull` keeps them
current.

## Auth setup

The jar stays local — never inside the clone. Create a local auth directory
from the examples in the pack (`docs/auth-setup.md`):

```bash
mkdir -p ~/.config/whatsapp-auth
cd "$BOTS_REPO_ROOT/grok_bots/whatsapp-bot"
cp _auth/AUTH_PATH.txt.example _auth/AUTH_PATH.txt
cp _auth/PERSONAL_PATH.txt.example _auth/PERSONAL_PATH.txt
# edit the PATH files to point at ~/.config/whatsapp-auth
```

First run or dead session: ask the user to scan the QR interactively in the
runtime's browser (`https://web.whatsapp.com/`), wait until the chat list is
visible, then export cookies into `auth.env` (mode 0600). See
`docs/qr-link.md`. Re-QR on death the same way.

Auth check:

```bash
cd "$BOTS_REPO_ROOT/grok_bots/whatsapp-bot"
python3 auth-check/scripts/check.py
python3 auth-check/scripts/check.py --no-probe
```

Never print cookie or token **values**.

## Running tasks

WhatsApp Web traffic is largely **opaque** (WebSocket / protobuf). Do **not**
invent private HTTP APIs. Pick a mode:

| Mode | Flag | When |
| --- | --- | --- |
| **Headless CDP** | `--mode=headless` | Linked Chrome on `DISPLAY`; structured JSON |
| **browser** | `--mode=browser` | Fallback when DOM selectors break |
| **HTTP replay** | `--mode=http` | Only after a real capture fills `capture/endpoints.json` (else exits `TRAFFIC_OPAQUE`) |

Examples:

```bash
cd "$BOTS_REPO_ROOT/grok_bots/whatsapp-bot"
export DISPLAY=:30
export NODE_OPTIONS=--experimental-websocket

python3 chats-list/scripts/list_chats.py --mode=headless --limit 5
python3 messages-read/scripts/read_messages.py --mode=headless --chat "Note to self" --limit 5
python3 chats-search/scripts/search_chats.py --mode=headless --query alice
# mutating — dry-run without --confirm
python3 message-send/scripts/send.py --mode=headless --chat "Note to self" --text "hello"
python3 message-send/scripts/send.py --mode=headless --chat "Note to self" --text "hello" --confirm
```

## Safety rules

- Mutating scripts require **`--confirm`**. Without it they dry-run.
- No mass messaging or spam tooling.
- Never invent WhatsApp private API endpoints or chat state.
- No secrets in git, chat, or logs. Never print cookie/token values.

## Offline verification

```bash
cd "$BOTS_REPO_ROOT/grok_bots/whatsapp-bot"
python3 auth-check/scripts/check.py --no-probe
python3 -c 'from _lib.auth import load; print(sorted(load().keys()))'
```
