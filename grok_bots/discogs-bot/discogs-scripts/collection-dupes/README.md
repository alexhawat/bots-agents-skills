# collection-dupes

Wave 2 — find releases with ×2+ copies in the collection.

## Endpoint

Same as collection-export / collection-search: `ViewerCollectionListData` persisted query (sha256 from 2026-09-05 capture). See `capture/SOURCE.md` and `_lib/collection_fetch.py`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie.

## CLI

```bash
cd discogs-scripts
uv run python collection-dupes/scripts/dupes.py
uv run python collection-dupes/scripts/dupes.py --limit 200   # debug / partial scan
uv run python collection-dupes/scripts/dupes.py --folder-id 0 --min-count 2
```

Groups by `release_id`, prints count, title, artists, each collection item id + folder + addedAt.
