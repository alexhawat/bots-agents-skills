# cart-list-remove

Wave 4 — list (read-only) + remove (confirm). LIVE 2026-09-05.

## Endpoints

| Action | Method | URL |
|--------|--------|-----|
| list | GET | `https://www.discogs.com/sell/cart/` |
| remove | GET | `https://www.discogs.com/sell/cart/?remove={listingId}` |

List parses HTML lightly for listing ids / prices (`?remove=`, `/sell/item/`, `span.price`).

Capture: `../../wantlist-add-remove/capture/wave4.har`. See `capture/SOURCE.md`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie.

## CLI

```bash
cd discogs-scripts
uv run python cart-list-remove/scripts/cart.py list
uv run python cart-list-remove/scripts/cart.py list --json
uv run python cart-list-remove/scripts/cart.py remove --listing-id 4345527582
uv run python cart-list-remove/scripts/cart.py remove --listing-id 4345527582 --confirm
```
