# collection-folders

Wave 3 — list collection folders and item counts (read-only).

**Move between folders is Wave 4 / confirm later — not implemented.**

## Endpoint

`ViewerCollectionListData` persisted query (sha from collection-search 2026-09-05). Folder edges: `discogsId`, `name`, `totalCount`. See `capture/SOURCE.md`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie.

## CLI

```bash
cd discogs-scripts
uv run python collection-folders/scripts/list_folders.py
uv run python collection-folders/scripts/list_folders.py --json
```
