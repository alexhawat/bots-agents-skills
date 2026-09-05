# collection-by-label-year-format

Wave 2 — client-side facet filters on collection export fields.

## Endpoint

Same GraphQL as collection-search (`ViewerCollectionListData`). Filters run locally on fetched rows (label / year / format are not separate API ops in the capture).

## Auth

`/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 collection-by-label-year-format/scripts/filter.py --format Vinyl --year 1980
python3 collection-by-label-year-format/scripts/filter.py --label RCA --year-min 1970 --year-max 1979
python3 collection-by-label-year-format/scripts/filter.py --format Vinyl --limit 200
```

- `--label SUBSTR` — case-insensitive match on primary label name
- `--year YYYY` or `--year-min` / `--year-max` — from release `released`
- `--format Vinyl` — match format **name** or **description** (e.g. LP)
- optional `--search` for server-side narrowing before local filters
