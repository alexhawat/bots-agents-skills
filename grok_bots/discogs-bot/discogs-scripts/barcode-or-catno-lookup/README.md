# barcode-or-catno-lookup

Wave 2 — catalog number / barcode → Discogs release (site autocomplete + public API).

## Endpoints

1. **Autocomplete** (captured `capture/barcode.har`, `capture/curls.txt`):
   `GET https://www.discogs.com/service/search-component/public/api/autocomplete?search=…&search_type=MASTER,RELEASE,ARTIST,LABEL&currency=EUR`  
   Returns `{autocomplete:[{__typename, discogsId, title, siteUrl, primaryArtists, formats, released, country, …}]}`.

2. **Public search** (documented; same pattern as price-suggest):
   `GET https://api.discogs.com/database/search?catno=…&type=release`  
   or `barcode=…&type=release`  
   User-Agent: `DiscogsScripts/1.0` (no Cookie).

3. **Optional in-collection** (`--check-collection`): GraphQL `UserReleaseData`  
   sha256=`a5c6a6cf7e06b6a9d43ab71e49f9e0e4ecb0f204d0db43a63d0f279075bd06e4`  
   (same as price-suggest).

Shared helpers: `_lib/discogs_search.py`.

## Auth

`/home/box/discogs-auth/auth.env` via `_lib/auth.py` for autocomplete (optional) and collection check. Never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 barcode-or-catno-lookup/scripts/lookup.py DMO-55454
python3 barcode-or-catno-lookup/scripts/lookup.py --catno DMO-55454
python3 barcode-or-catno-lookup/scripts/lookup.py --barcode 0724361234567
python3 barcode-or-catno-lookup/scripts/lookup.py DMO-55454 --check-collection
```

Expect release **18197845** for `DMO-55454`.

## Capture

See `capture/` — redacted curls + HAR from signed-in search for `DMO-55454`.
