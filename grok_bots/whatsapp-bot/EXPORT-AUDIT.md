# Export audit

Generated for `/workspace/whatsapp-scripts-public/` (mirror of live `/workspace/whatsapp-scripts/`).

## Included
- Script shapes for waves 0–4 + Wave H headless libs
- README, PLAN, EXPORT, AUTOMATION-BACKLOG
- docs: auth-setup, qr-link, headless-chrome, browser-path
- `_auth/*.example` only
- Redacted fixtures (`*-redacted.json`, sample batch YAML/JSON)
- `tools/capture_network.mjs` (helper copied from live `out/`; no live JSON)
- `TREE.txt` (this pack file list)

## Excluded (intentionally)
- `out/` entire directory (live samples, probes, network dumps, pycache)
- `_auth/AUTH_PATH.txt` and `_auth/PERSONAL_PATH.txt` (real pointers)
- `__pycache__/`, `*.pyc`, `.DS_Store`
- `.git/` (fresh repo init for public push)
- Any real session env files (never lived in the scripts tree)

## Still private (not in pack)
- Box-local auth jar under `/home/box/whatsapp-auth/`
- Live Chrome profile / linked session

## Audit
Run the `rg` checklist from the parent task / `EXPORT.md` pre-push section against this pack.
Expect: zero hits on personal chat content / cookie **values**.
Cookie **names** in docs (documentation only) are OK.

## Audit result

Personal-content / cookie-value checklist: **zero hits** (2026-09-07).
GitHub: https://github.com/alexhawat/whatsapp-scripts (public).
