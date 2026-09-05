# Capture notes — missing-from-series

- Date: 2026-09-05
- Public API only for series resolution (no new GraphQL ops):
  - `GET /releases/{id}` → `series`
  - `GET {series.resource_url}/releases` (paginated) or `GET /database/search?type=release&q=…`
- Collection ownership: existing `ViewerCollectionListData` via `_lib/collection_fetch.py`
  sha `ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b`
- Cookies/secrets redacted; never log Cookie.
