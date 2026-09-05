# collection-export

Wave 2 — dump signed-in Discogs collection to CSV + JSON.

## Endpoint (existing capture)

`GET https://www.discogs.com/service/catalog/api/graphql`

- `operationName=ViewerCollectionListData`
- sha256Hash=`ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b`
- variables: `page`, `perPage` (50), `currency=EUR`, `folderId` (0=all), `direction=DESC`, `field=ADDED`, `search` (empty = full dump)

Capture source: `../collection-search/capture/` (see `capture/SOURCE.md`). Shared paginator: `_lib/collection_fetch.py`.

## Auth

`/home/box/discogs-auth/auth.env` via `_lib/auth.py` (never print Cookie).

## CLI

```bash
cd /workspace/discogs-scripts
python3 collection-export/scripts/export.py --limit 100
python3 collection-export/scripts/export.py --folder-id 0 --search ""
python3 collection-export/scripts/export.py --search "Federico" --limit 50
```

Outputs under `collection-export/out/`: `collection-YYYYMMDD-HHMMSS.csv` + `.json`.

Columns: `collection_item_id, release_id, title, artists, year, format, label, catno, folder, added_at, url`.
