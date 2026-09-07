# Export / public surface (WhatsApp-Bot)

## Safe to publish (GitHub + Grok Bot template)
- Scrubbed persona (no phone, no names, no cookies)
- Skill: `whatsapp-capture-to-script` procedure (when published)
- `/workspace/whatsapp-scripts/` script **shapes**, README, PLAN, AUTOMATION-BACKLOG, EXPORT.md
- `_lib/` loaders + headless CDP helpers (paths only; no session dumps)
- `_auth/AUTH_PATH.txt.example` / `PERSONAL_PATH.txt.example`
- Redacted fixtures only (`*-redacted.json`, sample batch YAML/JSON with fake names)
- `docs/` runbooks (`auth-setup`, `qr-link`, `headless-chrome`, `browser-path`)
- `tools/capture_network.mjs` (helper only — never live capture JSON)

## Never publish
- Local auth jar (`auth.env`, `personal.env`, cookies, localStorage dumps)
- Chat transcripts, media, phone numbers from live captures
- HAR / network dumps with session tokens
- `_auth/AUTH_PATH.txt` / `PERSONAL_PATH.txt` (real pointers — use `.example` only)
- `out/*` live samples (`chats-list-sample.json`, `wa-dom-probe.json`, etc.)

## Wave H headless status (2026-09-07)

| Item | Public-ready? | Notes |
| --- | --- | --- |
| `_lib/headless_cdp.mjs`, `wa_dom.mjs`, `run_headless.mjs`, `headless_runner.py` | **Ready** | Code + docs; no secrets |
| `--mode=headless` on chats-list / messages-read / chats-search / message-send | **Ready** | Shape + CLI; needs local linked Chrome |
| `docs/headless-chrome.md` | **Ready** | Redacted example chat names |
| Auth jar (session file with cookies / UA) | **Still private** | Box-local only; never in GitHub |
| Live `out/*.json` probes / samples | **Still private** | Gitignored; excluded from export pack |
| Real HTTP replay endpoints | **Not ready** | Capture empty (`opaque_ws`); do not invent |

## Public pack path
Clean mirror (for push): `/workspace/whatsapp-scripts-public/`  
(Live working tree remains `/workspace/whatsapp-scripts/` with `out/` gitignored.)

## Intended GitHub layout
`github.com/alexhawat/whatsapp-scripts` (**public**):
```
README.md
EXPORT.md
PLAN.md
AUTOMATION-BACKLOG.md
.gitignore
_lib/
_auth/AUTH_PATH.txt.example
_auth/PERSONAL_PATH.txt.example
<slug>/...
docs/
tools/capture_network.mjs
```

Public Grok Bot template = scrubbed CreateAgent description + skill pointer + "bring your own QR session".

## Pre-push checklist
- [ ] `rg` audit for personal chat names / cookie values → zero hits
- [ ] No `out/` live samples in the pack
- [ ] Only `*_PATH.txt.example` under `_auth/`
- [ ] README installable by strangers (no personal names)
- [ ] Auth jar remains outside the repo
