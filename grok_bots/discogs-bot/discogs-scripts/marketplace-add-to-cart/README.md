# marketplace-add-to-cart

Wave 4 — mutate (hard confirm). LIVE 2026-09-05.

## Endpoint

Navigation GET (not GraphQL):

`GET https://www.discogs.com/sell/cart/?add={listingId}`

Optional tracking `ev=` seen in capture — omitted by the script (not required).

**Hard confirm:** both `--confirm` and `--i-really-mean-it` are required.

Capture: `capture/wave4.har` + curls in wantlist-add-remove. See `capture/SOURCE.md`.

## Auth

`/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
# dry-run (exit 2) — missing either flag
python3 marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 4345527582
python3 marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 4345527582 --confirm
# live (both flags)
python3 marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 4345527582 --confirm --i-really-mean-it
```
