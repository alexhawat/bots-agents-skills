---
name: Discogs capture to script
description: >-
  Use when reverse-engineering Discogs browser tasks into scripts, refreshing
  the Discogs Cookie jar (/home/box/discogs-auth), syncing Live inventory with
  /workspace/discogs-scripts, or preparing an exportable Discogs-Bot share —
  never paste cookies into chat.
---
# Discogs capture → script

Use when reverse-engineering a Discogs (or similar) browser task into a script: capture network once with session auth, then replay APIs and skip the UI next time. Also use when prioritizing Discogs-Bot backlog items, refreshing the Discogs Cookie jar, or preparing an exportable share (procedure only — never secrets).

## Goal

One expensive browser/computer-use run → capture requests → script under a task folder → later runs hit APIs directly with the same session auth. Re-capture only on auth death or API drift. Discogs-Bot runs the live automations under `/workspace/discogs-scripts/` on demand.

## Shared auth (owned by Discogs-Bot)

**Canonical jar (box-local, never export):** `/home/box/discogs-auth/auth.env`  
**Personal overrides (box-local, never export):** `/home/box/discogs-auth/personal.env` (`USERNAME`, `CURRENCY`, …)  
Pointer: `/workspace/discogs-scripts/_auth/AUTH_PATH.txt` → auth.env. Optional: `PERSONAL_PATH.txt` → personal.env.  
Loader: `/workspace/discogs-scripts/_lib/auth.py` merges auth.env → personal.env → task-local → override.

### First-time / dead session (self-serve)
1. Open `https://www.discogs.com/` with **browserUse** (Discogs-Bot’s own Chrome session).
2. If login, 2FA, or captcha: `request_box_help`. The user types secrets on the desktop. Never ask for password/2FA in chat.
3. When signed-in nav (username menu) is visible, **auto-import** the jar:
   - Prefer: `python3 /home/box/discogs-auth/export_cookies.py` (writes `COOKIE=` + `USER_AGENT=`, mode 0600).
   - Order inside the exporter: (1) **this-display live CDP** via `export_from_display.mjs` (`DISPLAY` → `SAND_BOX_CDP_PORT_BASE + N`, `Storage.getCookies`) — required because the shared `chrome-cookie-seed.json` is box-global and can be stale; (2) seed fallback (`/home/box/agent-data/chrome-cookie-seed.json`); (3) best-effort Chrome SQLite decrypt (usually fails here — no `os_crypt` key).
   - Or save the request `Cookie` header into `/home/box/discogs-auth/auth.env` during a HAR/capture (never paste into chat).
4. Run `auth-refresh` (`--check-only`) before failing tasks on dead session (`viewer=null`). Re-export with `export_cookies.py` / `auth-refresh` (without `--check-only`) after login.
5. Scripts load COOKIE from the shared jar first; username/currency from `personal.env`.

### Hard rules for secrets
- Never paste Cookie / Authorization values into chat, persona, skill text, or shareable templates.
- Do not commit `auth.env` or `personal.env`. README/EXPORT.md may document paths only.
- Export templates: include this skill’s *procedure* + script shapes — never the jar or personal file.

## Hard rules (capture / replay)

- Do not invent endpoints. Only use captured URLs/methods/bodies (or a public API the user explicitly asked for).
- **Mutating** calls: confirm one line first. Cart add = hard confirm (`--confirm` + `--i-really-mean-it`). Checkout/payment stays a human browser step.
- Prefer page-level browser; computer-use when DevTools/HAR needs the desktop.
- **Do not build backlog items until the user asks.**

## Backlog

Source of truth: `/workspace/discogs-scripts/AUTOMATION-BACKLOG.md`.  
Persona live list: Discogs-Bot `// version 4.2` (source of truth: `PERSONA.md`).  
Exportable surface: `docs/EXPORT.md`.

**Live** (on disk under `/workspace/discogs-scripts/<slug>/scripts/`, shared Cookie — inventory 2026-09-05, matches persona v4.2):

| slug | script |
| --- | --- |
| `collection-search` | `search_collection.py` |
| `marketplace-search` | `search.py` |
| `release-listings` | `listings.py` |
| `wantlist-search` | `search.py` |
| `wantlist-vs-marketplace` | `compare.py` |
| `price-suggest` | `suggest.py` |
| `mywantlist-search` | `search.py` |
| `collection-export` | `export.py` |
| `collection-dupes` | `dupes.py` |
| `collection-by-label-year-format` | `filter.py` |
| `barcode-or-catno-lookup` | `lookup.py` |
| `vinyl-photo-identify` | `identify.py` (hybrid vision/OCR + lookup) |
| `whoami-profile-stats` | `whoami.py` |
| `collection-folders` | `list_folders.py` (list/counts only) |
| `artist-discography-search` | `discography.py` |
| `master-vs-release` | `master_vs_release.py` |
| `compare-pressings` | `compare.py` |
| `wantlist-add-remove` | `wantlist.py` (mutates; `--confirm`) |
| `collection-add-remove` | `collection.py` (mutates; `--confirm`) |
| `collection-notes` | `notes.py` (mutates; `--confirm`) |
| `marketplace-add-to-cart` | `add_to_cart.py` (hard confirm: `--confirm` + `--i-really-mean-it`) |
| `cart-list-remove` | `cart.py` (list free; remove needs `--confirm`) |
| `orders-list` | `orders.py` (purchases list + order status; read-only) |
| `auth-refresh` | `refresh.py` (`--check-only` / re-export Cookie) |
| `har-diff` | `diff.py` (HAR/curls vs expected GraphQL shas) |
| `batch-runner` | `batch.py` (`search collection|wantlist|market`) |
| `missing-from-series` | `missing.py` |

Shared libs: `_lib/` (`auth.py`, `http.py`, `mp_html.py`, `collection_fetch.py`, `discogs_search.py`, `graphql_mutate.py`, …).

**Not live (deferred):** seller-inventory-search, digest routines, image→release (catalog), export-for-insurance/value, wantlist-notifications-poll.

**Leave to human browser / UI session:** checkout/payment, seller messaging, heavy one-off browse without a script goal. Discogs-Bot does not depend on Discogs Manager for auth.

## Steps

1. Ensure shared auth jar is fresh (section above); auto-import Cookie after login.
2. Name the task slug; folder `/workspace/discogs-scripts/<slug>/`.
3. Capture once (HAR / copy-as-cURL); drop noise.
4. Script loads `/home/box/discogs-auth/auth.env` (+ `personal.env`); redacted stdout.
5. Verify once; reuse until 401/403 → re-login path + refresh jar.
6. After shipping new slugs: update this **Live** table, add tests for any new pure
   parser, and bump the Discogs-Bot persona the same turn (minor).

## Output

Script path + endpoints (no secret values) + redacted sample. Cite paths + dates.
