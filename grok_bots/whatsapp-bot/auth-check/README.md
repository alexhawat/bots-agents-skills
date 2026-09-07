# auth-check

Wave 0 — prove `auth.env` has required key names (never print values).

## What it does
1. Loads `/home/box/whatsapp-auth/auth.env` via `_lib.auth.load()`.
2. Requires keys **COOKIE** and **USER_AGENT** present (prints key names only).
3. Optional `--export`: runs `python3 /home/box/whatsapp-auth/export_cookies.py` then re-checks.
4. Optional weak HTTP probe: `GET https://web.whatsapp.com/` with Cookie header; reports **status code only**.
   - **200 ≠ fully authenticated** for WhatsApp Web (page HTML can load without a live linked session).

## Exit codes
| code | meaning |
| --- | --- |
| 0 | required keys present → `ok keys=[...]` |
| 1 | missing keys → `dead missing=...` |

## Full session proof
Chat list visible in Chrome on `https://web.whatsapp.com/`. On death: reopen QR via `qr-link` + `auth-export`.

## CLI
```bash
cd /workspace/whatsapp-scripts
python3 auth-check/scripts/check.py
python3 auth-check/scripts/check.py --export
python3 auth-check/scripts/check.py --no-probe
```
