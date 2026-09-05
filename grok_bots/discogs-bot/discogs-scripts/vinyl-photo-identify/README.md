# vinyl-photo-identify

Wave 2 — **hybrid** image / text → Discogs release candidates → optional collection check.

There is **no** Discogs image-search API. This script does not invent one.

## Hybrid flow

1. Input: image path(s) and/or `--query` text.
2. If images given: run `tesseract` OCR when installed; otherwise note that **Grok Bot** can `Read` the image (vision) and pass `--query`.
3. Extract likely catalog numbers / barcodes (alphanumeric + dashes) and free-text artist/title hints.
4. Search via shared `_lib/discogs_search.py`:
   - site autocomplete (`/service/search-component/public/api/autocomplete`)
   - public `api.discogs.com/database/search`
5. Optional `--check-collection`: `UserReleaseData` GraphQL (sha from price-suggest).
6. Print ranked candidates with in-collection yes/no.

If tesseract is missing, the script still works with `--query` alone.

## Agent + script usage

```text
User drops sleeve photo
  → Grok Bot Reads image (vision) → crafts --query "Artist Title CATNO"
  → python3 vinyl-photo-identify/scripts/identify.py --query '…' --check-collection
```

Or with local OCR:

```bash
python3 vinyl-photo-identify/scripts/identify.py ./sleeve.jpg --check-collection
python3 vinyl-photo-identify/scripts/identify.py ./sleeve.jpg --query 'extra hint text'
```

## Auth

`/home/box/discogs-auth/auth.env` via `_lib/auth.py` for session autocomplete + collection. Public search uses User-Agent `DiscogsScripts/1.0` only. Never print Cookie.

## CLI examples

```bash
cd /workspace/discogs-scripts
python3 vinyl-photo-identify/scripts/identify.py --query 'Lucio Demare DMO-55454'
python3 vinyl-photo-identify/scripts/identify.py --query 'Lucio Demare DMO-55454' --check-collection
```

Expect release **18197845** among top candidates for the Demare / DMO-55454 query.

## Related

- `barcode-or-catno-lookup` — pure catno/barcode CLI (same search helpers)
- Capture for autocomplete: `../barcode-or-catno-lookup/capture/`
