# WhatsApp-Bot (public pack)

Session-backed automations for **WhatsApp Web**. Link once with QR, then run
read/write scripts via headless CDP or browser UI automation. Slug folders over a
shared `_lib/`, plus auth-path examples (secrets stay on your machine).

**Repo:** https://github.com/alexhawat/bots-agents-skills
**Path:** `grok_bots/whatsapp-bot/`
**License:** MIT (repo root)

This folder is the **public** script shapes + docs. Never commit live cookies,
`auth.env`, chat transcripts, or unredacted captures.

## Requirements

- **Python 3.10+** (stdlib preferred for task scripts)
- **Node 20+** for headless CDP helpers (`_lib/*.mjs`, `tools/capture_network.mjs`)
- A linked WhatsApp Web session (QR once; jar stays local)

## Quick start (from this monorepo)

```bash
git clone https://github.com/alexhawat/bots-agents-skills.git
cd bots-agents-skills/grok_bots/whatsapp-bot
# Python 3.10+ and Node 20+ recommended
```

### Auth jar (local only — never commit)

Create a local auth directory from the examples (see [`docs/auth-setup.md`](docs/auth-setup.md)):

```bash
mkdir -p /home/box/whatsapp-auth   # or any path you prefer
# copy auth.env.example / personal.env.example into that dir
# point the loaders:
cp _auth/AUTH_PATH.txt.example _auth/AUTH_PATH.txt
cp _auth/PERSONAL_PATH.txt.example _auth/PERSONAL_PATH.txt
# edit the PATH files if your auth dir is elsewhere
```

### Link WhatsApp Web once (QR)

Follow [`docs/qr-link.md`](docs/qr-link.md): open `https://web.whatsapp.com/`, scan
the QR (`request_box_help` on a Grok Bot box), wait until the chat list is visible,
then export cookies into `auth.env`.

### Auth check

```bash
python3 auth-check/scripts/check.py
python3 auth-check/scripts/check.py --no-probe
python3 -c 'from _lib.auth import load; print(sorted(load().keys()))'
```

Never print cookie or token **values**. On death: re-run QR link → export → re-check.

## Install on a Grok Bot box

1. Import the WhatsApp-Bot **public template** in Grok Bot (persona + skill + memories). The card does **not** include the script tree.
2. Copy this pack onto the box (matches the card `// install`):

```bash
# from a clone of alexhawat/bots-agents-skills
cp -a grok_bots/whatsapp-bot/. /workspace/whatsapp-scripts/
```

3. Auth jar lives at `/home/box/whatsapp-auth/` (examples + exporters; **never** ship live `auth.env`).
4. QR-link WhatsApp Web in **that** bot's Chrome (`request_box_help` — see `docs/qr-link.md`).
5. `python3 /home/box/whatsapp-auth/export_cookies.py`
6. `python3 /workspace/whatsapp-scripts/auth-check/scripts/check.py`
7. From the pack examples: `cp _auth/AUTH_PATH.txt.example _auth/AUTH_PATH.txt` (and `PERSONAL_PATH` the same way) so loaders point at the jar.

## Running scripts

WhatsApp Web traffic is largely **opaque** (WebSocket / protobuf). Do **not** invent
private HTTP APIs. Prefer:

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

## Never commit / never ship

Live `auth.env`, `personal.env`, cookies, localStorage dumps, chat transcripts,
media, phone numbers, or unredacted HARs. Only `_auth/*_PATH.txt.example` ships;
real path pointers stay gitignored. See [`EXPORT.md`](EXPORT.md).

## Docs

| Doc | Purpose |
| --- | --- |
| [`PERSONA.md`](PERSONA.md) | Scrubbed storefront + charter (public template)
| [`EXPORT.md`](EXPORT.md) | What is safe to publish vs must stay private |
| [`PLAN.md`](PLAN.md) | Product plan + public track |
| [`AUTOMATION-BACKLOG.md`](AUTOMATION-BACKLOG.md) | Wave status |
| [`docs/auth-setup.md`](docs/auth-setup.md) | Create local auth jar from examples |
| [`docs/qr-link.md`](docs/qr-link.md) | QR link + cookie export runbook |
| [`docs/headless-chrome.md`](docs/headless-chrome.md) | Headless CDP (`--mode=headless`) |
| [`docs/browser-path.md`](docs/browser-path.md) | browserUse fallback when HTTP is opaque |
| [`docs/whatsapp-capture-to-script.SKILL.md`](docs/whatsapp-capture-to-script.SKILL.md) | Capture→script skill prose |

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

Layout per slug: `README.md`, `capture/SOURCE.md`, `capture/endpoints.json`,
`scripts/<name>.py` (runbooks may omit scripts).

## Hard rules

- Never invent WhatsApp private API endpoints.
- Mutating scripts require `--confirm`.
- No mass messaging / spam tooling.
- Secrets stay in your local auth directory only (never in this pack).
