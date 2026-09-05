# compare-pressings

Wave 3 — given a master (or release→master), list pressings and mark which are in your collection.

## Endpoints

- Public versions: `GET /masters/{id}/versions`
- Ownership: `_lib.discogs_search.check_in_collection` → GraphQL `UserReleaseData` (same sha as price-suggest)

Caps version checks with `--limit` (default 30) and sleeps lightly between calls.

## Auth

Required for collection checks: `$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie.

## CLI

```bash
cd discogs-scripts
uv run python compare-pressings/scripts/compare.py --release-id 18197845 --limit 10
uv run python compare-pressings/scripts/compare.py --master-id 4253358 --limit 30
```

Table: release id, country, format, catno, year, in_collection yes/no.
