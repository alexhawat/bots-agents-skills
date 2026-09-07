# chats-list

Wave 1 — list recent chats (name, unread, last preview).

## Modes
| mode | behavior |
| --- | --- |
| `browser` (default) | Print browserUse procedure; no network calls |
| `headless` | CDP DOM via agent's linked Chrome — real JSON chats (see `docs/headless-chrome.md`) |
| `http` | Exit **2** `TRAFFIC_OPAQUE` unless `capture/endpoints.json` has real captured URLs |

## Source of truth (SoT)
- headless_live = Live
- opaque_ws = HTTP empty
- http_replay = blocked until real endpoints

## CLI
```bash
cd /workspace/whatsapp-scripts
export DISPLAY=:30
python3 chats-list/scripts/list_chats.py
python3 chats-list/scripts/list_chats.py --mode=browser
python3 chats-list/scripts/list_chats.py --mode=headless --limit 5
python3 chats-list/scripts/list_chats.py --mode=http   # refuses until capture

# or node directly
NODE_OPTIONS=--experimental-websocket node _lib/run_headless.mjs list-chats --limit 5
```

## Capture rule
Do not invent WhatsApp private API endpoints. Fill `capture/endpoints.json` only from live CDP/HAR. Prefer `--mode=headless` while traffic stays opaque WS/protobuf.
