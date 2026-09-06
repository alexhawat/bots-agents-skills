# wantlist-search

Wave 1 — live 2026-09-05.

## Endpoint
`GET https://www.discogs.com/api/shop-page-api/sell_item`  
**Capture surface:** wantlist-for-sale feed (`/sell/mywants` shop page) — listings matching your wantlist, not a free-text catalog search of the wantlist itself.

Working query params: `count`, `offset`, `sort` (`listedDate`|`price`), `sortOrder` (`ascending`|`descending`), `sellerRatingMin`, `currency`, `formatName`, `shipsFrom`, `facets=true`.  
**Do not send** `fast` or `wants` (HTTP 422).

Response: `items[]`, `totalCount`. Item fields include `itemId`, `price{amount,currencyCode,buyerItemPrice,buyerCurrencyCode}`, `release{releaseId,title,artists[{name}],formatNames}`, `seller`, `mediaCondition`, `sleeveCondition`, `listedDate`.

Text search (`q`) is **client-side** filter on title/artists — API has no `q`.

## Auth
`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`)

## CLI
```bash
cd discogs-scripts
uv run python wantlist-search/scripts/search.py --q tango --count 50 --format-name Vinyl --currency EUR
uv run python wantlist-search/scripts/search.py --format-name Vinyl --seller-rating-min 90
```
