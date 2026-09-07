# Capture notes — chats-list

- **Date:** 2026-09-07
- **Method:** CDP `Network.enable` via `out/capture_network.mjs` (DISPLAY=:30)
- **Evidence:**
  - `/workspace/whatsapp-scripts/out/wa-network-capture.json`
  - `/workspace/whatsapp-scripts/out/wa-network-summary.md`
- **Result:** empty — `events=0`, `endpoints=0`
- **Cookie names only (no values):** `wa_ul`, `wa_web_access_token`, `wa_web_lang_pref`
- **Status:** `opaque_ws_protobuf`
- **Conclusion:** no REST/GraphQL WhatsApp private HTTP APIs observed; traffic is opaque (likely long-lived WebSocket/protobuf established before capture). **Do not invent endpoints.**
- **Operational path:** browserUse UI until a future capture proves HTTP.
- **endpoints.json:** `status=opaque_ws`, `endpoints=[]` (see real capture source above)

- Note: Chat list sync expected over WS/protobuf — HTTP replay blocked until a future capture proves otherwise.

## Headless DOM selectors (2026-09-07 probe)
- Evidence: `out/wa-dom-probe.json`
- `#pane-side`, `[data-testid="chat-list"]`, `[data-testid="cell-frame-container"]`
- Title: `[data-testid="cell-frame-title"] span[title]`
- Time / preview / unread: `cell-frame-primary-detail`, `cell-frame-secondary`, `icon-unread-count`
- Operational path: `--mode=headless` via `_lib/run_headless.mjs` (Wave H) in addition to browserUse.
