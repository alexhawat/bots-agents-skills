# collection-folders

Wave 3 — list collection folders and item counts (read-only).

**Move between folders is Wave 4 / confirm later — not implemented.**

## Endpoint

`ViewerCollectionListData` persisted query (sha from collection-search 2026-09-05). Folder edges: `discogsId`, `name`, `totalCount`. See `capture/SOURCE.md`.

## Auth

`/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 collection-folders/scripts/list_folders.py
python3 collection-folders/scripts/list_folders.py --json
```
