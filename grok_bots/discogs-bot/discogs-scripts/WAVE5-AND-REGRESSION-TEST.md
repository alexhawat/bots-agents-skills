# Wave 5 build + regression test plan
Prepared 2026-09-05 by dr eggbot for Discogs Scripts.
Source of truth for live slugs: AUTOMATION-BACKLOG.md + discogs-capture-to-script Live table.

## A. Build Wave 5 first (then bump via eggbot)
21. `orders-list` / `order-status` — buyer orders, read-only
22. `auth-refresh` — re-export Cookie when `viewer=null` (semi-manual; Manager/desktop for login if needed)
23. `har-diff` — detect endpoint drift vs captured expectations
24. `batch-runner` — one CLI wrapping scripts: `search collection|wantlist|market --q …`
25. `missing-from-series` — have vol 1,3 of X → what’s missing

Mark AUTOMATION-BACKLOG Wave 5 LIVE when done. Report paths + redacted endpoints to eggbot for **3.5 → 3.6** bump + skill Live sync. Do **not** start deferred-past-wave-5 items.

## B. Regression test rules
- Jar: `/home/box/discogs-auth/auth.env`. Never print secrets.
- Cwd: `/workspace/discogs-scripts` (PYTHONPATH / `_lib` as each script expects).
- **Reads:** run for real; record pass/fail + 1-line sample (counts/ids, no cookies).
- **Mutates (wave 4):** default = **dry-run only** (omit `--confirm` → expect exit 2 + planned text).  
  Live mutates only if Alex already OK’d in chat; prefer reversible wantlist add→remove on a throwaway release; **never** live cart-add unless Alex says so.
- Vinyl photo: use `--query` text path if no image (OCR optional).
- Write results to `/workspace/discogs-scripts/out/regression-YYYYMMDD-HHMM.md` (+ optional `.json`) with columns: wave, slug, request, cmd, exit, pass/fail, notes.
- When done: ping eggbot with that path so eggbot renders **HTML from anything** (`report` template).

## C. Request list (chat phrasing → CLI)

### Wave 1 + extra (read)
1. Search my collection for `kraftwerk` (vinyl only)  
   `python3 collection-search/scripts/search_collection.py kraftwerk --vinyl-only`
2. Marketplace search `basic channel` vinyl EUR  
   `python3 marketplace-search/scripts/search.py "basic channel" --format Vinyl --currency EUR`
3. Listings for release `249504` (or first id from a prior search)  
   `python3 release-listings/scripts/listings.py 249504`
4. Wantlist-for-sale feed, client filter `techno`, ships NL  
   `python3 wantlist-search/scripts/search.py techno --ships-from Netherlands --count 20`
5. Wantlist deals under €25  
   `python3 wantlist-vs-marketplace/scripts/compare.py --max-price 25 --currency EUR --limit 15`
6. Price suggest for same release id  
   `python3 price-suggest/scripts/suggest.py 249504`
7. My wantlist HTML search `aphex`  
   `python3 mywantlist-search/scripts/search.py aphex`

### Wave 2
8. Export collection sample (limit 50)  
   `python3 collection-export/scripts/export.py --limit 50`
9. Find duplicate releases  
   `python3 collection-dupes/scripts/dupes.py --min-count 2`
10. Filter collection: vinyl, year ≥ 1990, label contains `warp`  
    `python3 collection-by-label-year-format/scripts/filter.py --format Vinyl --year-min 1990 --label warp`
11. Lookup catno / barcode (pick a real one from export or `WARP`)  
    `python3 barcode-or-catno-lookup/scripts/lookup.py --catno WARP --check-collection --limit 10`
12. Identify from text query (photo path optional)  
    `python3 vinyl-photo-identify/scripts/identify.py --query "Aphex Twin Selected Ambient Works" --check-collection`

### Wave 3
13. Who am I + folder stats  
    `python3 whoami-profile-stats/scripts/whoami.py --json`
14. List collection folders  
    `python3 collection-folders/scripts/list_folders.py --json`
15. Artist discography `Jeff Mills`  
    `python3 artist-discography-search/scripts/discography.py "Jeff Mills" --per-page 25`
16. Master vs release for a known release id  
    `python3 master-vs-release/scripts/master_vs_release.py --release-id 249504`
17. Compare pressings (limit 10)  
    `python3 compare-pressings/scripts/compare.py --release-id 249504 --limit 10`

### Wave 4 (dry-run default)
18. Wantlist add dry-run  
    `python3 wantlist-add-remove/scripts/wantlist.py add --release-id 249504`  # expect exit 2
19. Wantlist remove dry-run  
    `python3 wantlist-add-remove/scripts/wantlist.py remove --release-id 249504`
20. Collection add dry-run  
    `python3 collection-add-remove/scripts/collection.py add --release-id 249504`
21. Collection remove dry-run (needs item id from export — substitute)  
    `python3 collection-add-remove/scripts/collection.py remove --item-id ITEM_ID`
22. Collection notes set dry-run  
    `python3 collection-notes/scripts/notes.py set --item-id ITEM_ID --note-type 3 --text "wave5-regression-dry"`
23. Cart list (read)  
    `python3 cart-list-remove/scripts/cart.py list`
24. Cart add dry-run (fake or real listing id)  
    `python3 marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 123456789`  # expect exit 2 without hard flags
25. Cart remove dry-run  
    `python3 cart-list-remove/scripts/cart.py remove --listing-id 123456789`

### Wave 5 (after build — adapt to real CLIs)
26. List buyer orders / one order status  
27. Auth-refresh: simulate or run when viewer null; document semi-manual path  
28. HAR-diff against a recent capture or bundled fixture  
29. Batch-runner: `search collection|wantlist|market --q kraftwerk` (exact CLI from build)  
30. Missing-from-series for a series you partially own (or dry fixture)

## D. Report handoff
Ping eggbot with `/workspace/discogs-scripts/out/regression-….md` (+ wave 5 LIVE note). Eggbot runs html-from-anything → `/workspace/html-from-anything/…html`.
