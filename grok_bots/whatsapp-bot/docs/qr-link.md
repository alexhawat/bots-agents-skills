# QR link runbook

Link WhatsApp Web **once** on the bot Chrome, then export cookies into the local auth jar.

## Steps

1. Open the agent desktop / browserUse and go to `https://web.whatsapp.com/`.
2. If a QR code is shown, call **`request_box_help`** so the human can scan with their phone (WhatsApp → Linked devices).
3. Wait until the **chat list** is visible — that is full session proof.
4. Export cookies (auth-export):

```bash
python3 /home/box/whatsapp-auth/export_cookies.py
# or the display-aware CDP helper if present:
# node /home/box/whatsapp-auth/export_from_display.mjs
```

5. Verify keys only (never print values):

```bash
cd /workspace/whatsapp-scripts
python3 auth-check/scripts/check.py --no-probe
python3 -c 'from _lib.auth import load; print(sorted(load().keys()))'
```

## Re-link when session dies

Signs: `auth-check` fails, headless exits **1** (`not_linked`), or Chrome shows the QR again.

1. Re-run this runbook (`request_box_help` scan).
2. Re-export cookies.
3. Re-check; optionally `node _lib/probe_dom.mjs` → `linked: true`.

## Safety

- Do not paste QR screenshots with phone numbers into public logs or GitHub.
- Secrets land only under the local auth directory (see `docs/auth-setup.md`).
- Linking is UI-only — no private HTTP API.
