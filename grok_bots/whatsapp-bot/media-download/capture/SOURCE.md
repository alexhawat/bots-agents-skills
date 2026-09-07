# Capture notes — media-download

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

- Note: Media fetch may still be opaque binary over WS/CDN — do not invent URLs; browserUse until capture proves HTTP.
