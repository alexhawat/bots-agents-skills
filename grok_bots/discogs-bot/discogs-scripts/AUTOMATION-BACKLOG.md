# Discogs Scripts — automation backlog

Saved 2026-09-05. **Do not build from this list until asked.**  
Existing: `collection-search` (GraphQL `ViewerCollectionListData`, live-verified).

Owner: Discogs Scripts (903704f2…) = capture → script → API replay.  
UI browse/checkout stays human browser / optional UI bot — Discogs-Bot owns auth + scripts.

## Named backlog
1. **marketplace-search** — filter listings (artist/title/format/price/ships-from/condition)
2. **marketplace-add-to-cart** — add a chosen listing (confirm before mutate)
3. **wantlist-search** — search/filter wantlist
4. **vinyl-photo-identify** — image → Discogs match → check if already in *your* collection (vision + search/collection lookup; hybrid, not pure API)

## Collection
5. **collection-folders** — list folders / counts / move item between folders
6. **collection-add / collection-remove** — add or remove a release (confirm)
7. **collection-notes** — set media/sleeve condition, notes
8. **collection-export** — dump folder or full collection to CSV/JSON
9. **collection-dupes** — find releases with ×2+ copies
10. **collection-by-label / year / format** — facet-style queries beyond free text

## Wantlist
11. **wantlist-add / wantlist-remove**
12. **wantlist-vs-marketplace** — wantlist items with active listings under a max price
13. **wantlist-notifications-poll** — cheap check for new matches (routine fodder)

## Marketplace / buying
14. **release-listings** — all sellers for one release (sort by price/condition)
15. **cart-list / cart-remove**
16. **orders-list / order-status** — buyer orders (read-only first)
17. **seller-inventory-search** — if selling later
18. **price-suggest** — stats for a release (have/want, last sold) before buying

## Catalog / identity
19. **artist-discography-search** — masters/releases for an artist (site/catalog GraphQL)
20. **barcode-or-catno-lookup** — scan/cat# → release
21. **master-vs-release** — pick pressing variants
22. **whoami / profile-stats** — quick identity + collection value snapshot

## Cross-cutting
23. **auth-refresh** — re-export Cookie when `viewer=null` (semi-manual)
24. **har-diff** — detect endpoint drift after Discogs deploys
25. **batch-runner** — one CLI: `search collection|wantlist|market --q …` wrapping scripts
26. **digest routines** — e.g. daily: wantlist under €X; new listings for watched artists
27. **image→release (catalog)** — photo ID against Discogs DB, not only collection
28. **compare-pressings** — given a master, list owned variants
29. **missing-from-series** — “I have vol 1,3 of X — what’s missing”
30. **export-for-insurance / value** — collection value snapshot over time

## Leave to human browser / UI (rare)
- Login, 2FA, captcha, checkout/payment, messaging sellers, listing creation with heavy form UI, one-off browse

## Proven so far (collection-search)
- Collection-scoped GraphQL search matches release + **track** text (fuzzy), e.g. song `La bruja`.
- `--artist-match` filters primary artists only — drops pure song hits; use raw search for track titles.
- Auth: session Cookie in task `auth.env` (gitignored). HAR often omits cookies.

## Highest leverage next (suggested priority)
1. `marketplace-search` + `release-listings`
2. `wantlist-search` + `wantlist-vs-marketplace`
3. `vinyl-photo-identify` (collection check)
4. `collection-export` / `collection-dupes`
5. `marketplace-add-to-cart` (hard confirm)

## For dr eggbot / persona improvements
- Encode this backlog in Discogs Scripts profile or a skill checklist (capture order, mutate = confirm).
- Clarify hybrid tasks (photo ID) vs pure replay.
- Keep single-owner rule: scripts here, heavy UI elsewhere.
- Optional: standing auth-refresh / har-diff routines once marketplace scripts exist.

## Waves (2026-09-05) — 5×5, max 5 waves

`collection-search` already live — not in a wave. **Build only the active wave** until the user says next.

### Wave 1 — marketplace + wantlist read (LIVE 2026-09-05)
1. `marketplace-search` — live → `marketplace-search/scripts/search.py` (`GET /sell/list` HTML)
2. `release-listings` — live → `release-listings/scripts/listings.py` (summary API + `/sell/release/{id}` HTML)
3. `wantlist-search` — live → `wantlist-search/scripts/search.py` (`GET /api/shop-page-api/sell_item`; client-side q)
4. `wantlist-vs-marketplace` — live → `wantlist-vs-marketplace/scripts/compare.py` (same feed; buyerItemPrice ≤ max)
5. `price-suggest` — live → `price-suggest/scripts/suggest.py` (market summary + UserReleaseData + public `/releases/{id}`)

### Wave 2 — collection intel + ID (LIVE 2026-09-05)
6. `collection-export` — live → `collection-export/scripts/export.py` (ViewerCollectionListData → CSV/JSON)
7. `collection-dupes` — live → `collection-dupes/scripts/dupes.py` (group by release_id, ×2+)
8. `collection-by-label` / year / format — live → `collection-by-label-year-format/scripts/filter.py`
9. `vinyl-photo-identify` (hybrid) — live → `vinyl-photo-identify/scripts/identify.py` (OCR/`--query` → `_lib/discogs_search` + optional UserReleaseData)
10. `barcode-or-catno-lookup` — live → `barcode-or-catno-lookup/scripts/lookup.py` (autocomplete + public `/database/search`; optional `--check-collection`)

### Wave 3 — catalog + identity (LIVE 2026-09-05)
11. `artist-discography-search` — live → `artist-discography-search/scripts/discography.py` (autocomplete + public `/artists/{id}/releases`)
12. `master-vs-release` — live → `master-vs-release/scripts/master_vs_release.py` (public `/releases` `/masters` `/versions`; optional DeferredReleaseData)
13. `compare-pressings` — live → `compare-pressings/scripts/compare.py` (versions + UserReleaseData via `check_in_collection`; `--limit` default 30)
14. `whoami` / profile-stats — live → `whoami-profile-stats/scripts/whoami.py` (UserCollectionPageData + ViewerCollectionListData + optional ViewerCollectionPageData)
15. `collection-folders` — live → `collection-folders/scripts/list_folders.py` (list/counts only; move = Wave 4 / confirm later)

### Wave 4 — mutates (LIVE 2026-09-05; confirm each)
16. `wantlist-add` / `wantlist-remove` — live → `wantlist-add-remove/scripts/wantlist.py` (AddReleasesToWantlist / RemoveReleasesFromWantlist)
17. `collection-add` / `collection-remove` — live → `collection-add-remove/scripts/collection.py` (AddReleaseToCollection / RemoveReleaseFromCollection; remove = item id)
18. `collection-notes` — live → `collection-notes/scripts/notes.py` (EditCollectionItemNote / RemoveCollectionItemNote; type 3 = free text in capture)
19. `marketplace-add-to-cart` (hard confirm) — live → `marketplace-add-to-cart/scripts/add_to_cart.py` (`GET /sell/cart/?add=`; needs `--confirm` + `--i-really-mean-it`)
20. `cart-list` / `cart-remove` — live → `cart-list-remove/scripts/cart.py` (`GET /sell/cart/` list; `?remove=` mutate)

### Wave 5 — ops + stretch (LIVE 2026-09-05)
21. `orders-list` / `order-status` — live → `orders-list/scripts/orders.py` (`list` / `status`; GET `/sell/purchases`, `/sell/order/{id}` HTML)
22. `auth-refresh` — live → `auth-refresh/scripts/refresh.py`
23. `har-diff` — live → `har-diff/scripts/diff.py`
24. `batch-runner` — live → `batch-runner/scripts/batch.py`
25. `missing-from-series` — live → `missing-from-series/scripts/missing.py`

**Deferred past wave 5:** seller-inventory-search, digest routines, image→release (catalog), export-for-insurance/value, wantlist-notifications-poll.
