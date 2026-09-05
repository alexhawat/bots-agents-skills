# Manual smoke tests

Run-by-hand checks against a **live** signed-in session — the counterpart to the
offline `make test` suite, which needs no auth. Use this after a Discogs deploy,
after refreshing the cookie jar, or before publishing a change to the pack.

Automated equivalents that need no session:

```bash
make test      # unit tests over the pure parsers
make smoke     # offline HAR replay + har-diff, no network
```

## Rules
- Jar: `$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`). Never print secrets.
- Cwd: `discogs-scripts/` (each script puts the pack root on `sys.path` for `_lib`).
- **Reads:** run for real; record pass/fail + 1-line sample (counts/ids, no cookies).
- **Mutates (wave 4):** default = **dry-run only** (omit `--confirm` → expect exit 2 + planned text).  
  Live mutates only if the operator has OK’d it in chat; prefer reversible wantlist add→remove on a throwaway release; **never** live cart-add unless the operator says so.
- Vinyl photo: use `--query` text path if no image (OCR optional).
- Write results to `out/regression-YYYYMMDD-HHMM.md` (+ optional `.json`) with columns: wave, slug, request, cmd, exit, pass/fail, notes.

## Request list (chat phrasing → CLI)

### Wave 1 + extra (read)
1. Search my collection for `kraftwerk` (vinyl only)  
   `uv run python collection-search/scripts/search_collection.py kraftwerk --vinyl-only`
2. Marketplace search `basic channel` vinyl EUR  
   `uv run python marketplace-search/scripts/search.py "basic channel" --format Vinyl --currency EUR`
3. Listings for release `249504` (or first id from a prior search)  
   `uv run python release-listings/scripts/listings.py 249504`
4. Wantlist-for-sale feed, client filter `techno`, ships NL  
   `uv run python wantlist-search/scripts/search.py techno --ships-from Netherlands --count 20`
5. Wantlist deals under €25  
   `uv run python wantlist-vs-marketplace/scripts/compare.py --max-price 25 --currency EUR --limit 15`
6. Price suggest for same release id  
   `uv run python price-suggest/scripts/suggest.py 249504`
7. My wantlist HTML search `aphex`  
   `uv run python mywantlist-search/scripts/search.py aphex`

### Wave 2
8. Export collection sample (limit 50)  
   `uv run python collection-export/scripts/export.py --limit 50`
9. Find duplicate releases  
   `uv run python collection-dupes/scripts/dupes.py --min-count 2`
10. Filter collection: vinyl, year ≥ 1990, label contains `warp`  
    `uv run python collection-by-label-year-format/scripts/filter.py --format Vinyl --year-min 1990 --label warp`
11. Lookup catno / barcode (pick a real one from export or `WARP`)  
    `uv run python barcode-or-catno-lookup/scripts/lookup.py --catno WARP --check-collection --limit 10`
12. Identify from text query (photo path optional)  
    `uv run python vinyl-photo-identify/scripts/identify.py --query "Aphex Twin Selected Ambient Works" --check-collection`

### Wave 3
13. Who am I + folder stats  
    `uv run python whoami-profile-stats/scripts/whoami.py --json`
14. List collection folders  
    `uv run python collection-folders/scripts/list_folders.py --json`
15. Artist discography `Jeff Mills`  
    `uv run python artist-discography-search/scripts/discography.py "Jeff Mills" --per-page 25`
16. Master vs release for a known release id  
    `uv run python master-vs-release/scripts/master_vs_release.py --release-id 249504`
17. Compare pressings (limit 10)  
    `uv run python compare-pressings/scripts/compare.py --release-id 249504 --limit 10`

### Wave 4 (dry-run default)
18. Wantlist add dry-run  
    `uv run python wantlist-add-remove/scripts/wantlist.py add --release-id 249504`  # expect exit 2
19. Wantlist remove dry-run  
    `uv run python wantlist-add-remove/scripts/wantlist.py remove --release-id 249504`
20. Collection add dry-run  
    `uv run python collection-add-remove/scripts/collection.py add --release-id 249504`
21. Collection remove dry-run (needs item id from export — substitute)  
    `uv run python collection-add-remove/scripts/collection.py remove --item-id ITEM_ID`
22. Collection notes set dry-run  
    `uv run python collection-notes/scripts/notes.py set --item-id ITEM_ID --note-type 3 --text "wave5-regression-dry"`
23. Cart list (read)  
    `uv run python cart-list-remove/scripts/cart.py list`
24. Cart add dry-run (fake or real listing id)  
    `uv run python marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 123456789`  # expect exit 2 without hard flags
25. Cart remove dry-run  
    `uv run python cart-list-remove/scripts/cart.py remove --listing-id 123456789`

### Wave 5 (after build — adapt to real CLIs)
26. List buyer orders / one order status  
27. Auth-refresh: simulate or run when viewer null; document semi-manual path  
28. HAR-diff against a recent capture or bundled fixture  
29. Batch-runner: `search collection|wantlist|market --q kraftwerk` (exact CLI from build)  
30. Missing-from-series for a series you partially own (or dry fixture)

## Report handoff

Write results to `out/regression-YYYYMMDD-HHMM.md` (gitignored) with columns:
wave, slug, request, cmd, exit, pass/fail, notes.
