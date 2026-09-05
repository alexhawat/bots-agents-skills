# release-listings

Wave 1 — live 2026-09-05.

## Endpoints
1. Summary JSON: `GET https://www.discogs.com/api/shop-page-api/market/release/{releaseId}`  
   Keys: `artistName`, `currency`, `format`, `listingsCount`, `priceRangeMax`, `priceRangeMin`, `title`, `thumbnailUrl`.
2. Listings HTML: `GET https://www.discogs.com/sell/release/{releaseId}`  
   Same `tr.shortcut_navigable` row pattern as marketplace-search.

## Auth
`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`)

## CLI
```bash
cd discogs-scripts
uv run python release-listings/scripts/listings.py 7146198
```
