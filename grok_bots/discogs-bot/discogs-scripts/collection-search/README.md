# collection-search

Search the signed-in Discogs collection by text (same as the collection `searchParam` UI).

## Capture (2026-09-05)

- Username: `$USERNAME`
- UI: `https://www.discogs.com/user/$USERNAME/collection?searchParam=<q>`
- API (HAR): `GET https://www.discogs.com/service/catalog/api/graphql`
  - `operationName=ViewerCollectionListData`
  - variables: `page`, `perPage`, `currency`, `folderId` (0=all), `direction`, `field` (`ADDED`), `search`
  - persistedQuery sha256: `ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b`
- Artifacts: `capture/collection-federico.har`, `capture/curls.txt`, `capture/browser-pass-2026-09-05.md`
- Auth: local `auth.env` (`COOKIE=...`) — gitignored. HAR export stripped cookies; export Cookie from DevTools when session dies.

## Auth

Prefer shared jar: `/home/box/discogs-auth/auth.env` (Discogs-Bot shared jar). Task-local `auth.env` is fallback.

## Run

```bash
# write auth.env first (COOKIE=... from DevTools Request Headers)
python3 scripts/search_collection.py 'Domingo Federico' --vinyl-only --artist-match 'Federico'
```

Flags: `--vinyl-only`, `--artist-match SUBSTR`, `--json`.

Live verified 2026-09-05 with session Cookie in `auth.env` (Domingo Federico → 12 unique / 17 rows).

Re-capture auth only on `viewer=null` / HTTP 401/403.

Chrome HAR exports often omit Cookie. For live replay, copy Cookie from DevTools → Network into `auth.env` (see `auth.env.example`). Offline check:

```bash
python3 scripts/search_collection.py 'Domingo Federico' --vinyl-only --artist-match Federico \
  --from-har capture/collection-federico.har
```
