# marketplace-add-to-cart

Wave 4 — mutate (hard confirm). LIVE 2026-09-05.

## Endpoint

Navigation GET (not GraphQL):

`GET https://www.discogs.com/sell/cart/?add={listingId}`

Optional tracking `ev=` seen in capture — omitted by the script (not required).

**Hard confirm:** both `--confirm` and `--i-really-mean-it` are required.

Capture: `../../wantlist-add-remove/capture/wave4.har` + curls in wantlist-add-remove. See `capture/SOURCE.md`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie.

## CLI

```bash
cd discogs-scripts
# dry-run (exit 2) — missing either flag
uv run python marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 4345527582
uv run python marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 4345527582 --confirm
# live (both flags)
uv run python marketplace-add-to-cart/scripts/add_to_cart.py --listing-id 4345527582 --confirm --i-really-mean-it
```
