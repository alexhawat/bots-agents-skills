# marketplace-search

Wave 1 — live 2026-09-05.

## Endpoint
`GET https://www.discogs.com/sell/list`  
Query params (verified): `format`, `q`, `currency` (+ `page` for pagination).  
HTML: `tr.shortcut_navigable` rows with `data-release-id`, `/sell/item/{id}`, `span.price` (`data-currency`, `data-pricevalue`), `a.item_description_title`, `data-seller-username`.

## Auth
Shared jar: `/home/box/discogs-auth/auth.env` (task `auth.env` overrides if present).

## CLI
```bash
cd /workspace/discogs-scripts
python3 marketplace-search/scripts/search.py Pugliese --format Vinyl --currency EUR
python3 marketplace-search/scripts/search.py Pugliese --format Vinyl --page 2
```
