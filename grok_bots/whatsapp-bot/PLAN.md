# WhatsApp-Bot — plan (Discogs-Bot pattern, public next)

**Owner bot:** WhatsApp-Bot (Grok Bot)  
**Scripts root:** `/workspace/whatsapp-scripts/`  
**Public export pack:** `/workspace/whatsapp-scripts-public/`  
**Secrets root (box-local):** `/home/box/whatsapp-auth/`  
**Status:** v1 scaffold + auth-check + QR path done; HTTP replay blocked on opaque traffic; browserUse + **headless CDP** paths are Live

## Product idea
Same loop as Discogs-Bot:
1. User links WhatsApp Web **once** via QR on the bot's Chrome (`request_box_help`).
2. Bot exports durable session artifacts (never into chat).
3. Capture a named task's network once → script under `whatsapp-scripts/<slug>/`.
4. Later runs replay with session auth; re-QR only on death.
5. Publish scrubbed template + GitHub scripts (no secrets) as the next public bot.

## Auth model
| Piece | Where | Export? |
| --- | --- | --- |
| Chrome linked session | Bot's shared-box Chrome profile | No |
| Session file (`auth.env`) | `/home/box/whatsapp-auth/` | Never |
| `personal.env` | same | Never |
| Pointer files | `whatsapp-scripts/_auth/*_PATH.txt` | Paths only (`.example` in public) |

First-time:
1. browserUse → `https://web.whatsapp.com/`
2. QR / device confirm → `request_box_help` (user scans phone)
3. When chat list visible → export helper (CDP cookies first; document IndexedDB/localStorage if cookies alone fail)
4. `auth-check` before failing tasks

## Technical reality (plan honestly)
WhatsApp Web is **not** Discogs GraphQL. Expect:
- Heavy **WebSocket / binary protobuf** traffic
- Session often more than HTTP cookies
- Some tasks stay **browserUse UI automation** until a stable captured replay exists
Rule: **do not invent endpoints** — only captured URLs/frames or explicit documented public APIs.

### Capture evidence (2026-09-07)
- Evidence: live-tree `out/` capture summary (not in public pack)
- Method: DISPLAY CDP `Network.enable` via `tools/capture_network.mjs`
- Result: `events=0`, `endpoints=0`; cookie **names** only (no values in docs)
- Conclusion: **no REST/GraphQL WhatsApp private HTTP APIs observed**; traffic is opaque (likely long-lived WebSocket/protobuf)
- Operational path: **headless CDP** (preferred) + **browserUse UI** fallback for Wave 1+ until a future capture proves HTTP (see `docs/browser-path.md`, `docs/headless-chrome.md`)

## Public / GitHub track
1. [x] Keep persona scrubbed from day one (no phone, no personal names in charter).
2. [x] Grow `whatsapp-scripts` like `discogs-scripts`; `EXPORT.md` is the share checklist.
3. [x] README installable by strangers; wave 0+1 scripts + headless Live.
4. [x] Export pack at `/workspace/whatsapp-scripts-public/` (rsync mirror; audit before push).
5. [x] Land public pack in `alexhawat/bots-agents-skills` at `grok_bots/whatsapp-bot/`.
6. [ ] Grok Bot **Share as template** after secrets audit (same bar as Discogs-Bot export).
7. [ ] Version scripts + bot with `/workspace/bot-versions` (`// version` minors per wave).
8. Path B (alternate HTTP / unofficial API claims): **on ice** — do not invent endpoints; revisit only after a real capture proves HTTP.

## Success criteria for v1
- [ ] Bot created, on-demand wake, house-rules + freshness
- [x] Scaffold + backlog + export rules on disk
- [ ] Skill `whatsapp-capture-to-script` live
- [x] QR link path documented (`qr-link` / `docs/qr-link.md`); local session file; `auth-check` script passes on keys
- [x] Scripts scaffolded for waves 0–4 (skeletons + opaque HTTP gate)
- [x] First network capture attempted (2026-09-07) — **empty** (`endpoints=0`); HTTP replay **blocked** on opaque WS/protobuf
- [x] browserUse operational path documented (`docs/browser-path.md`) — Live for Wave 1+ until endpoints appear
- [x] Headless CDP Live (`docs/headless-chrome.md`, `--mode=headless`)
- [x] Public export pack prepared (`/workspace/whatsapp-scripts-public/`)
- [ ] First read script with **real HTTP endpoints** — still N/A; only when a future capture proves HTTP (do not invent)
- [x] Public pack live — https://github.com/alexhawat/bots-agents-skills/tree/main/grok_bots/whatsapp-bot

## Anti-goals
- No unofficial "WhatsApp Business API" claims without Meta credentials
- No mass messaging / spam tooling
- No secrets in persona, skill, GitHub, or chat
- No invented private API URLs

## Live status (2026-09-07)

- QR linked; session file exported locally (mode 0600) — **private**
- CDP Network capture: 0 private HTTP endpoints → `opaque_ws`
- Scripts scaffolded for Waves 0–4; `--mode=http` refuses without capture
- Browser path verified for Wave 1–3 read/media/contact flows
- message-send: confirm-gated; live send verified on Note-to-self; mark-read still confirm-gated / not live-tested
- Wave 4: har-diff + batch-runner scripts present
- **Wave H — headless Chrome (CDP):** `_lib/headless_cdp.mjs` + `wa_dom.mjs` + `run_headless.mjs`; `--mode=headless` on chats-list / messages-read / chats-search / message-send. Verified list-chats returns titles on linked display. Docs: `docs/headless-chrome.md`.
- **Public pack:** `/workspace/whatsapp-scripts-public/` — see `EXPORT.md`
