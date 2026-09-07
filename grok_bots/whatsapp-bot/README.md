# whatsapp-scripts

Session-backed automations for **WhatsApp Web**. Link once with QR, then run read/write scripts via headless CDP or browser UI automation.

This repo is the **public** script shapes + docs. Secrets stay on your machine only.

## Quick start

### 1. Install

```bash
git clone https://github.com/alexhawat/whatsapp-scripts.git
cd whatsapp-scripts
# Python 3.10+ and Node 20+ recommended
```

### 2. Auth jar (local only — never commit)

Create a local auth directory from the examples (see [`docs/auth-setup.md`](docs/auth-setup.md)):

```bash
mkdir -p /home/box/whatsapp-auth   # or any path you prefer
# copy auth.env.example / personal.env.example into that dir
# point the loaders:
cp _auth/AUTH_PATH.txt.example _auth/AUTH_PATH.txt
cp _auth/PERSONAL_PATH.txt.example _auth/PERSONAL_PATH.txt
# edit the PATH files if your auth dir is elsewhere
```

### 3. Link WhatsApp Web once (QR)

Follow [`docs/qr-link.md`](docs/qr-link.md): open `https://web.whatsapp.com/`, scan the QR (`request_box_help` on a Grok Bot box), wait until the chat list is visible, then export cookies into `auth.env`.

### 4. Auth check

```bash
python3 auth-check/scripts/check.py
python3 auth-check/scripts/check.py --no-probe
python3 -c 'from _lib.auth import load; print(sorted(load().keys()))'
```

Never print cookie or token **values**. On death: re-run QR link → export → re-check.

## Running scripts

WhatsApp Web traffic is largely **opaque** (WebSocket / protobuf). Do **not** invent private HTTP APIs. Prefer:

| Mode | Flag | When |
| --- | --- | --- |
| **Headless CDP** | `--mode=headless` | Linked Chrome on `DISPLAY`; structured JSON (Wave H) |
| **browserUse** | `--mode=browser` | Fallback when DOM selectors break |
| **HTTP replay** | `--mode=http` | Only after a real capture fills `capture/endpoints.json` (currently exits `TRAFFIC_OPAQUE`) |

Examples:

```bash
export DISPLAY=:30
export NODE_OPTIONS=--experimental-websocket

python3 chats-list/scripts/list_chats.py --mode=headless --limit 5
python3 messages-read/scripts/read_messages.py --mode=headless --chat "Note to self" --limit 5
python3 chats-search/scripts/search_chats.py --mode=headless --query alice
# mutating — dry-run without --confirm
python3 message-send/scripts/send.py --mode=headless --chat "Note to self" --text "hello"
python3 message-send/scripts/send.py --mode=headless --chat "Note to self" --text "hello" --confirm
```

Or call the Node runner directly (see [`docs/headless-chrome.md`](docs/headless-chrome.md)).

## Anti-spam / safety

- Mutating scripts require **`--confirm`**. Without it they dry-run.
- No mass messaging or spam tooling.
- No secrets in git, chat, or logs.

## Docs

| Doc | Purpose |
| --- | --- |
| [`EXPORT.md`](EXPORT.md) | What is safe to publish vs must stay private |
| [`PLAN.md`](PLAN.md) | Product plan + public track |
| [`AUTOMATION-BACKLOG.md`](AUTOMATION-BACKLOG.md) | Wave status |
| [`docs/auth-setup.md`](docs/auth-setup.md) | Create local auth jar from examples |
| [`docs/qr-link.md`](docs/qr-link.md) | QR link + cookie export runbook |
| [`docs/headless-chrome.md`](docs/headless-chrome.md) | Headless CDP (`--mode=headless`) |
| [`docs/browser-path.md`](docs/browser-path.md) | browserUse fallback when HTTP is opaque |

## Slug inventory

| wave | slug | kind | notes |
| --- | --- | --- | --- |
| 0 | `qr-link` | runbook | QR once via browser + help |
| 0 | `auth-export` | runbook | export cookies → `auth.env` |
| 0 | `auth-check` | script | keys present; optional weak probe |
| 1 | `chats-list` | script | `--mode=headless` Live; HTTP → TRAFFIC_OPAQUE |
| 1 | `messages-read` | script | `--chat` `--limit` · headless / browser |
| 1 | `chats-search` | script | `--query` · headless / browser |
| 2 | `message-send` | script | `--chat` `--text` `--confirm` |
| 2 | `message-mark-read` | script | `--chat` `--confirm` |
| 3 | `media-download` | script | `--message-id` `--out` |
| 3 | `contact-info` | script | `--chat` or `--jid` |
| 4 | `har-diff` | tool | URL set vs expected (empty after opaque capture) |
| 4 | `batch-runner` | tool | read-only YAML/JSON batches |
| H | `_lib/*headless*` | lib | CDP DOM runner — see headless-chrome.md |

Layout per slug: `README.md`, `capture/SOURCE.md`, `capture/endpoints.json`, `scripts/<name>.py` (runbooks may omit scripts).

## Hard rules

- Never invent WhatsApp private API endpoints.
- Mutating scripts require `--confirm`.
- No mass messaging / spam tooling.
- Secrets stay in your local auth directory only (never in this repo).
