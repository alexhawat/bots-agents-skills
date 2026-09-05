# collection-dupes

Wave 2 — find releases with ×2+ copies in the collection.

## Endpoint

Same as collection-export / collection-search: `ViewerCollectionListData` persisted query (sha256 from 2026-09-05 capture). See `capture/SOURCE.md` and `_lib/collection_fetch.py`.

## Auth

`/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 collection-dupes/scripts/dupes.py
python3 collection-dupes/scripts/dupes.py --limit 200   # debug / partial scan
python3 collection-dupes/scripts/dupes.py --folder-id 0 --min-count 2
```

Groups by `release_id`, prints count, title, artists, each collection item id + folder + addedAt.
