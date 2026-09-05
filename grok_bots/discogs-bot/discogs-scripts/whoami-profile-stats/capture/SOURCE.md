# Capture notes — whoami-profile-stats

- Date: 2026-09-05
- Primary HAR: `../../collection-search/capture/collection-federico.har`
- Ops verified live in that capture:
  - `UserCollectionPageData` sha `4ec9e7cf35dfd68831890df31e7c2d9c32a9d13274db0aaebfd49f7f0331cd96` vars `{"username":"YOUR_DISCOGS_USERNAME"}` → username, discogsId, avatarUrl, collectionPrivacy, wantlistPrivacy, isViewer
  - `ViewerCollectionListData` sha `ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b` → `totalCollectionCount`, `collectionFolders.edges[].node.{discogsId,name,totalCount}`
  - `ViewerCollectionPageData` sha `462fbd5e05a757bc5dde79635e33691c036119aea912c7d51c65e81154e4a2b7` vars `{currency, search}` → `collectionStats.{min,median,max}Value` (use `search:""` for unfiltered)
- Cookies/secrets redacted; never log Cookie.
