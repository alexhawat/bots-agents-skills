# auth-export

Wave 0 — **README-only runbook** pointing at the box-local export helper (no secrets in this tree).

## Procedure
After chat list is visible (`qr-link`):

```bash
python3 /home/box/whatsapp-auth/export_cookies.py
```

Then verify (key names only):

```bash
cd /workspace/whatsapp-scripts
python3 auth-check/scripts/check.py --no-probe
python3 -c 'from _lib.auth import load; print(sorted(load().keys()))'
```

## Where secrets live
- Written only to `/home/box/whatsapp-auth/auth.env` (mode 0600).
- Pointer: `whatsapp-scripts/_auth/AUTH_PATH.txt` → that path.
- **Never** print or copy COOKIE / token values into README, chat, logs, or GitHub.

## Helper details
See `/home/box/whatsapp-auth/README.md` and `export_cookies.py` (CDP jar first, then cookie seed fallback).
