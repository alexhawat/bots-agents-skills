# missing-from-series

Wave 5 — given a series name or a release in that series, list series members not yet in the signed-in collection.

## Approach (no invented GraphQL)

1. Public `GET https://api.discogs.com/releases/{id}` → `series[]` (`name`, `catno`, `resource_url`, `id?`)
2. If `resource_url` present, paginate `{resource_url}/releases` (series are usually label entities)
3. Else `database/search?type=release&q=SERIES` with soft title filter
4. Owned ids via `_lib/collection_fetch.py` (`ViewerCollectionListData`)

UA: `DiscogsScripts/1.0` (+ optional `--contact`).

## CLI

```bash
cd /workspace/discogs-scripts
python3 missing-from-series/scripts/missing.py --series "Blue Note The Complete" --limit-series 50
python3 missing-from-series/scripts/missing.py --release-id 249504 --limit-series 100
python3 missing-from-series/scripts/missing.py --series "Some Series" --json
```

Prints series name, owned count, missing releases (`id`, title, year, catno), short owned list.
