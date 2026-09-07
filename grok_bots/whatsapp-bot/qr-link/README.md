# qr-link

Wave 0 — **README-only runbook** (no script). Link WhatsApp Web once on the bot Chrome.

## Procedure
1. Ask the parent agent / box operator to use **browserUse** (or open the box Chrome desktop).
2. Navigate to `https://web.whatsapp.com/`.
3. If a QR is shown, call **`request_box_help`** so the user can scan with their phone.
4. Wait until the **chat list** is visible (that is full session proof).
5. Continue to `auth-export` (export cookies → `auth.env`).

## Notes
- Do not paste QR screenshots with phone numbers into public logs.
- Re-run this runbook when `auth-check` reports dead keys or Chrome shows the QR again.
- No HTTP private API — linking is UI-only.
