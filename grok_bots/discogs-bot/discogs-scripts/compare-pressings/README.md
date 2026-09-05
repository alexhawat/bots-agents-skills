# compare-pressings

Wave 3 — given a master (or release→master), list pressings and mark which are in your collection.

## Endpoints

- Public versions: `GET /masters/{id}/versions`
- Ownership: `_lib.discogs_search.check_in_collection` → GraphQL `UserReleaseData` (same sha as price-suggest)

Caps version checks with `--limit` (default 30) and sleeps lightly between calls.

## Auth

Required for collection checks: `/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 compare-pressings/scripts/compare.py --release-id 18197845 --limit 10
python3 compare-pressings/scripts/compare.py --master-id 4253358 --limit 30
```

Table: release id, country, format, catno, year, in_collection yes/no.
