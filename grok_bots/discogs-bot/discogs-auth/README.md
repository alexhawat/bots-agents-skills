# Discogs shared auth (box-local, not for export templates)

Canonical Cookie jar for Discogs-Bot script replay. Uses Discogs-Bot's own Chrome session on this box.

## Login (first time / when dead)
1. Open https://www.discogs.com/ in Discogs-Bot's Chrome (browserUse on this box).
2. If login/2FA/captcha: `request_box_help` — user types secrets on the desktop. Agent never sees them.
3. When the signed-in user nav is visible, refresh this jar — prefer `auth-refresh` which auto-runs `export_cookies.py`.

## Export order (`export_cookies.py`)
1. **This-display live CDP** — `export_from_display.mjs` (`node --experimental-websocket`): `DISPLAY=:N` → CDP port `9222+N`, `Storage.getCookies`, filter `discogs`, require `session` or `sid`. Writes `auth.env` (0600). Prefer this; the shared box seed can be stale across Chromes.
2. **Seed fallback** — `/home/box/agent-data/chrome-cookie-seed.json` (same inode as sand-data seed; filled by sand-cookie-persist ~5s).
3. **SQLite decrypt** — best-effort on `chrome-profile*/Default/Cookies` (usually fails on this box: no `os_crypt` key / keyring).

Never print Cookie values. Never paste into chat.

## Files
- `auth.env` — `COOKIE=`… and `USER_AGENT=`… (mode 0600). Never commit. Never include in export packs.
- `personal.env` — `USERNAME`, `CURRENCY`, … Mode 0600. Never commit. Never include in export packs.
- `export_cookies.py` — orchestrator (CDP → seed → decrypt).
- `export_from_display.mjs` — live jar writer for this agent's Chrome.

## Consumers (Discogs-Bot)
Scripts under `/workspace/discogs-scripts/<task>/` load via `_lib/auth.py` merge order:
1. `/home/box/discogs-auth/auth.env` (shared; COOKIE source)
2. `/home/box/discogs-auth/personal.env` (personal overrides; later wins for non-secrets)
3. task-local `auth.env` (optional)
4. explicit override path (optional)

Fail with “COOKIE missing — refresh auth.env / re-login via Discogs-Bot Chrome + request_box_help” when the jar is empty.

Pointers: `/workspace/discogs-scripts/_auth/AUTH_PATH.txt`, `PERSONAL_PATH.txt`.
