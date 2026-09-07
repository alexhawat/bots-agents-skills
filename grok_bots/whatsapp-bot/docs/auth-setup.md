# Auth setup (local jar)

WhatsApp session secrets stay **outside** this repo. Create a local auth directory from examples — never copy a real session file into git.

## Recommended layout

```
/home/box/whatsapp-auth/
  auth.env.example      # safe template (key names only)
  personal.env.example  # safe template
  auth.env              # real session — mode 0600 — NEVER commit
  personal.env          # optional overrides — NEVER commit
  export_cookies.py     # helper (box-local)
  README.md             # helper docs
```

On a Grok Bot box these files may already exist under `/home/box/whatsapp-auth/`. Elsewhere, create the directory and copy the `*.example` templates, then fill values after QR link.

## Point the scripts at your jar

```bash
cd /workspace/whatsapp-scripts   # or your clone
cp _auth/AUTH_PATH.txt.example _auth/AUTH_PATH.txt
cp _auth/PERSONAL_PATH.txt.example _auth/PERSONAL_PATH.txt
# edit if your paths differ from /home/box/whatsapp-auth/...
```

`_auth/AUTH_PATH.txt` and `PERSONAL_PATH.txt` are **gitignored**. Only the `.example` files ship publicly.

## After QR link

1. Follow `docs/qr-link.md` until the chat list is visible.
2. Run the export helper so `auth.env` is written (mode 0600).
3. `python3 auth-check/scripts/check.py --no-probe`

## Never

- Commit `auth.env`, `personal.env`, cookies, or token dumps
- Paste cookie/token **values** into chat, README, or issues
- Publish live `out/` capture samples with real chat names
