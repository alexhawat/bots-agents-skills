# collection-search

Search the signed-in Discogs collection by text (same as the collection `searchParam` UI).

## Capture (2026-09-05)

- Username: `$USERNAME`
- UI: `https://www.discogs.com/user/$USERNAME/collection?searchParam=<q>`
- API (HAR): `GET https://www.discogs.com/service/catalog/api/graphql`
  - `operationName=ViewerCollectionListData`
  - variables: `page`, `perPage`, `currency`, `folderId` (0=all), `direction`, `field` (`ADDED`), `search`
  - persistedQuery sha256: `ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b`
- Artifacts: `capture/collection-federico.har` (redacted fixture — cookies stripped, rows synthetic), `capture/curls.txt`, `capture/response-sample.json` (synthetic — response shape only)
- Auth: shared jar (`$DISCOGS_AUTH_ENV`) — gitignored. HAR exports strip cookies; re-export from DevTools when the session dies.

## Auth

Prefer the shared jar at `$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`).
Task-local `auth.env` and `--auth PATH` are fallbacks. See the root README for the
environment variables that let a plain clone use its own jar.

## Run

```bash
# write auth.env first (COOKIE=... from DevTools Request Headers)
uv run python scripts/search_collection.py 'Domingo Federico' --vinyl-only --artist-match 'Federico'
```

Flags: `--vinyl-only`, `--artist-match SUBSTR`, `--json`.

Live verified 2026-09-05 with session Cookie in `auth.env` (Domingo Federico → 12 unique / 17 rows).

Re-capture auth only on `viewer=null` / HTTP 401/403.

Chrome HAR exports often omit Cookie. For live replay, copy Cookie from DevTools → Network into `auth.env` (see `auth.env.example`).

**Offline check** — needs no auth and no network. `capture/collection-federico.har` is a redacted fixture (cookies stripped, collection rows synthetic over real public
releases) shipped so this path stays runnable from a clone; `make smoke` runs it:

```bash
uv run python scripts/search_collection.py 'Domingo Federico' \
  --from-har capture/collection-federico.har
```
