---
name: WhatsApp capture to script
description: >-
  Use when reverse-engineering WhatsApp Web into scripts, QR-linking the
  session, refreshing /home/box/whatsapp-auth, or preparing an exportable
  WhatsApp-Bot share — never paste session secrets into chat.
---
# WhatsApp capture → script

Use when reverse-engineering WhatsApp Web tasks into scripts, linking via QR,
refreshing `/home/box/whatsapp-auth`, syncing Live inventory with
`/workspace/whatsapp-scripts`, or preparing an exportable WhatsApp-Bot share —
never paste cookies/session into chat.

## Goal

One expensive browser run (QR once) → durable session jar → capture a named
task’s network → script under `/workspace/whatsapp-scripts/<slug>/` → later runs
prefer headless CDP (or replay captured HTTP if it exists). Re-QR only on auth
death. Prefer captured endpoints; fall back to browserUse when traffic is opaque
protobuf/WebSocket. Do **not** invent endpoints.

Persona version marker: WhatsApp-Bot `// version 4` (source of truth: `PERSONA.md`).

## Shared auth (owned by WhatsApp-Bot)

**Canonical jar (box-local, never export):** `/home/box/whatsapp-auth/auth.env`  
**Personal overrides (box-local, never export):** `/home/box/whatsapp-auth/personal.env`  
Pointers: `/workspace/whatsapp-scripts/_auth/AUTH_PATH.txt` (+ optional `PERSONAL_PATH.txt`)  
Loader: `/workspace/whatsapp-scripts/_lib/auth.py`  
Exporter: `python3 /home/box/whatsapp-auth/export_cookies.py` (live CDP → seed; mode 0600)

### First-time / dead session
1. Open `https://web.whatsapp.com/` with **browserUse** (this bot’s Chrome).
2. QR / device confirm → `request_box_help`. User scans with phone on the desktop. Never ask for QR secrets in chat.
3. When the chat list is visible: `python3 /home/box/whatsapp-auth/export_cookies.py`.
4. Run `auth-check` before failing tasks. Re-export after re-link.
5. Never paste Cookie / tokens into chat, persona, skill, or GitHub.

### Hard rules for secrets
- Never paste Cookie / Authorization values into chat, persona, skill text, or shareable templates.
- Do not commit `auth.env` or `personal.env`. README/EXPORT.md may document paths only.
- Export templates: include this skill’s *procedure* + script shapes — never the jar.

## Hard rules (capture / replay)

- Do not invent endpoints. Only use captured URLs/methods/bodies (or a public API the owner explicitly asked for).
- WhatsApp Web is often **opaque** (WS/protobuf) — say so; keep `--mode=headless` / browserUse until a real capture fills `capture/endpoints.json`.
- **Mutating** calls: require `--confirm`. No mass send / spam tooling.
- Prefer headless CDP when the session is linked; browserUse when DOM/API paths break.
- **Do not build backlog items until the owner asks.**

## Backlog

Source of truth: `/workspace/whatsapp-scripts/AUTOMATION-BACKLOG.md`.  
Exportable surface: `EXPORT.md` in this pack.

**Live** (on disk under `/workspace/whatsapp-scripts/<slug>/`, inventory aligned with persona v4):

| slug | kind | notes |
| --- | --- | --- |
| `qr-link` | runbook | QR once via browser + help |
| `auth-export` | runbook | export cookies → `auth.env` |
| `auth-check` | script | keys present; optional weak probe |
| `chats-list` | script | `--mode=headless`; HTTP → TRAFFIC_OPAQUE |
| `messages-read` | script | `--chat` `--limit` |
| `chats-search` | script | `--query` |
| `message-send` | script | `--chat` `--text` `--confirm` |
| `message-mark-read` | script | `--chat` `--confirm` |
| `media-download` | script | `--message-id` `--out` |
| `contact-info` | script | `--chat` or `--jid` |
| `har-diff` | tool | URL set vs expected |
| `batch-runner` | tool | read-only YAML/JSON batches |

Shared libs: `_lib/` (`auth.py`, `cli.py`, headless CDP helpers).

**Leave to human browser / UI session:** linking a new phone, heavy one-off browse without a script goal.

## Steps

1. Ensure shared auth jar is fresh (section above).
2. Name the task slug; folder `/workspace/whatsapp-scripts/<slug>/`.
3. Capture once (HAR / CDP); drop noise; never commit live dumps.
4. Script loads `/home/box/whatsapp-auth/auth.env` (+ `personal.env`); redacted stdout.
5. Verify once; reuse until auth death → re-QR + export.
6. After shipping new slugs: update this **Live** table and bump the persona the same turn (minor).

## Public share
Scrubbed persona + this skill procedure + script shapes. Never `auth.env`,
`personal.env`, HARs with tokens, or phone numbers from live chats. The Grok Bot
public template card ships persona + skill + memories only; the script tree is
this pack under `grok_bots/whatsapp-bot/`.
