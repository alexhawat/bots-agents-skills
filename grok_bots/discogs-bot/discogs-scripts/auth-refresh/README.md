# auth-refresh

Wave 5 — check signed-in Discogs session (`viewer`) and optionally re-export Cookie from Discogs-Bot's box Chrome.

## Endpoint

| Op | sha256 | vars |
|----|--------|------|
| `ViewerCollectionListData` | `ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b` | `page=1 perPage=1 currency=EUR folderId=0` (minimal ping) |

Same hash as whoami / collection-search. See `capture/SOURCE.md`.

## Auth

`/home/box/discogs-auth/auth.env` (+ `personal.env`) via `_lib/auth.py`. Never print Cookie.

On dead session, runs `python3 /home/box/discogs-auth/export_cookies.py` (unless `--check-only`) and re-checks — prefer this auto-import path after a successful desktop login.

## CLI

```bash
cd discogs-scripts
uv run python auth-refresh/scripts/refresh.py --check-only
uv run python auth-refresh/scripts/refresh.py
uv run python auth-refresh/scripts/refresh.py --force-export
```

Success: `ok viewer=<username or id>` exit 0. Failure: semi-manual path (Discogs-Bot Chrome + `request_box_help` desktop login; then re-run refresh for auto `export_cookies.py` → Cookie in `auth.env`) exit 1.
