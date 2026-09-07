# Headless Chrome path (Wave H)

Drive WhatsApp Web without browserUse GUI by attaching to this agent's already-linked Chrome over sand-host CDP helpers.

## How it works

1. Resolve CDP port: SAND_BOX_CDP_PORT_BASE (9222) + display number from DISPLAY.
   Example: DISPLAY=:30 maps to port 9252.
2. connectBrowser(port) from the sand-host CDP helper module.
3. Pick the best web.whatsapp.com page target (prefer title like (N) WhatsApp / chat-list DOM; skip interstitial tabs).
4. Target.attachToTarget then Runtime.evaluate DOM helpers in _lib/wa_dom.mjs.
5. Return structured JSON on stdout.

No invented WhatsApp private HTTP APIs. Never print session secret values.

## Requirements

- Linked WhatsApp Web session on the agent's Chrome (qr-link once).
- DISPLAY set to that agent's desktop (e.g. :30).
- Node 20: always run with NODE_OPTIONS=--experimental-websocket
  (Python _lib/headless_runner.py sets this automatically).

## CLI

```bash
cd /workspace/whatsapp-scripts
export DISPLAY=:30
export NODE_OPTIONS=--experimental-websocket

node _lib/run_headless.mjs list-chats --limit 5
node _lib/run_headless.mjs search-chats --query alice --limit 5
node _lib/run_headless.mjs read-messages --chat Alice --limit 10
# mutating — requires --confirm
node _lib/run_headless.mjs send-text --chat "Note to self" --text "hi" --confirm

python3 chats-list/scripts/list_chats.py --mode=headless --limit 5
python3 messages-read/scripts/read_messages.py --mode=headless --chat Alice --limit 5
python3 chats-search/scripts/search_chats.py --mode=headless --query alice
python3 message-send/scripts/send.py --mode=headless --chat "Note to self" --text "hi"   # dry-run
python3 message-send/scripts/send.py --mode=headless --chat "Note to self" --text "hi" --confirm
```

Exit codes: 0 ok · 1 auth/QR dead / not linked · 2 error / confirm missing.

## Modules

| path | role |
| --- | --- |
| `_lib/headless_cdp.mjs` | connectWa, evaluate, disconnect, assertLinked |
| `_lib/wa_dom.mjs` | listChats / searchChats / openChat / readMessages / sendText |
| `_lib/run_headless.mjs` | JSON CLI runner |
| `_lib/headless_runner.py` | Python subprocess wrapper |
| `_lib/probe_dom.mjs` | Redacted DOM probe (writes under out/ locally — gitignored) |

## Selectors (probe 2026-09-07)

Documented in `_lib/wa_dom.mjs` SOURCE header:

- `#pane-side`, `[data-testid="chat-list"]`
- `[data-testid="cell-frame-container"]`, cell-frame-title / primary-detail / secondary, icon-unread-count
- Search: `[data-testid="chat-list-search-container"] input[data-tab="3"]`
- Messages: `[data-testid="conversation-panel-messages"] [data-testid="msg-container"]`
- Compose: `[data-testid="conversation-compose-box-input"]`

## QR death to re-link

If assertLinked is false / exit 1 (not_linked):

1. Chat list / search missing; QR canvas or login prompt visible, or only interstitial tabs remain.
2. Re-run qr-link (request_box_help scan on phone).
3. Re-export session via auth-export if needed.
4. Re-probe: node _lib/probe_dom.mjs expecting linked true.

Multiple WA tabs are common; the connector scores targets and prefers the live chat-list page.

## vs browserUse

| | browserUse | headless CDP |
| --- | --- | --- |
| GUI automation | yes | no |
| Needs agent desktop | yes | yes (same Chrome) |
| Output | agent steps | structured JSON |
| Mutating | confirm | --confirm |

Prefer headless for scripted Wave 1 reads and gated sends; keep browserUse as fallback when DOM selectors break.
