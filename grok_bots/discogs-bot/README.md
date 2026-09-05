# Discogs-Bot (public pack)

Grok Bot template companion: scrubbed persona, skill, auth helpers, and automation scripts.

**Repo:** https://github.com/alexhawat/bots-agents-skills  
**Path:** `grok_bots/discogs-bot/`

## Install on a Grok Bot box

1. Import the Discogs-Bot **public template** in Grok Bot (persona + skill).
2. Copy this folder onto the box:

```bash
# from a clone of alexhawat/bots-agents-skills
cp -a grok_bots/discogs-bot/discogs-scripts/. /workspace/discogs-scripts/
cp -a grok_bots/discogs-bot/discogs-auth/. /home/box/discogs-auth/
# optional: keep docs with the skill you already imported
```

3. Sign in to Discogs in **that** bot’s Chrome (`request_box_help` for login/2FA).
4. `python3 /home/box/discogs-auth/export_cookies.py`
5. `python3 /workspace/discogs-scripts/auth-refresh/scripts/refresh.py --check-only` → expect `ok viewer=…`
6. Copy `discogs-auth/personal.env.example` → `/home/box/discogs-auth/personal.env` and set `USERNAME` + `CURRENCY`.

## Never commit / never ship
Live `auth.env`, `personal.env`, `chrome-cookie-seed.json`, unredacted HARs, or Cookie values.

## Layout
- `PERSONA.md` — storefront + scrubbed charter (for humans / template authors)
- `docs/` — capture/run skill + EXPORT notes
- `discogs-scripts/` — automation tree (`_lib/` + task scripts)
- `discogs-auth/` — cookie export helpers + `*.example` env files
