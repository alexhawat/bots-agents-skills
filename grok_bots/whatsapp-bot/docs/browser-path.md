# Browser path (Wave 1+)

Real CDP capture on 2026-09-07 (`out/wa-network-summary.md`, `out/wa-network-capture.json`) found **zero** WhatsApp private HTTP endpoints (`events=0`, `endpoints=0`). Cookie names only: `wa_ul`, `wa_web_access_token`, `wa_web_lang_pref`. Traffic is treated as **opaque** (likely long-lived WebSocket / protobuf established before the capture window).

## How the bot runs tasks today

Until a future capture proves REST/GraphQL (or other replayable HTTP) APIs, the bot uses **browserUse** UI automation for:

| slug | action |
| --- | --- |
| `chats-list` | open chat list, read names / unread / previews |
| `messages-read` | open a chat, read last N messages |
| `chats-search` | search UI for chats/contacts |
| `message-send` | type + send (`--confirm` required) |
| `message-mark-read` | open chat / mark read (`--confirm`) |
| `media-download` | open message media via UI |
| `contact-info` | open contact/profile pane |

Wave 0 (`qr-link`, `auth-export`, `auth-check`) stays session/setup; no private API replay.

## Script modes

For each Wave 1–3 slug with a script:

- `--mode=http` → exit **2** (`TRAFFIC_OPAQUE`) — `capture/endpoints.json` has `status=opaque_ws` and `endpoints=[]`. Do not invent URLs.
- `--mode=browser` → print the browserUse procedure from the slug README / this doc; the bot then drives Chrome.

## Re-capture

```bash
cd /workspace/whatsapp-scripts
# with WhatsApp Web already open on the capture display, e.g. DISPLAY=:30
node tools/capture_network.mjs
# review out/wa-network-summary.md — only then fill capture/endpoints.json
```

Rule: **never invent endpoints**. Only record URLs/frames actually observed.

## Related

- Headless CDP runner (no GUI): [`headless-chrome.md`](./headless-chrome.md) — Wave H
