# wantlist-vs-marketplace

Wave 1 — live 2026-09-05.

## Endpoint
Same as wantlist-search: `GET https://www.discogs.com/api/shop-page-api/sell_item`  
Sorts `price` ascending, paginates, keeps rows where `price.buyerItemPrice` ≤ `--max-price` (buyer currency, default EUR).

Capture surface: wantlist-for-sale feed. Do not send `fast`/`wants`.

## Auth
`/home/box/discogs-auth/auth.env`

## CLI
```bash
cd /workspace/discogs-scripts
python3 wantlist-vs-marketplace/scripts/compare.py --max-price 10 --format-name Vinyl
python3 wantlist-vs-marketplace/scripts/compare.py --max-price 25 --currency EUR --limit 20
```
