# Capture notes — missing-from-series

- Date: 2026-09-05
- Public API only for series resolution (no new GraphQL ops):
  - `GET /releases/{id}` → `series`
  - `GET {series.resource_url}/releases` (paginated) or `GET /database/search?type=release&q=…`
- Collection ownership: existing `ViewerCollectionListData` via `_lib/collection_fetch.py`
  sha `91302e22b3c6df22424a92c0ebab5c536ed0640a35c4d1cabbe736919b50dda9`
- Cookies/secrets redacted; never log Cookie.
