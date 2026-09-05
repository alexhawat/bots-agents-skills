# cart-list-remove

Wave 4 — list (read-only) + remove (confirm). LIVE 2026-09-05.

## Endpoints

| Action | Method | URL |
|--------|--------|-----|
| list | GET | `https://www.discogs.com/sell/cart/` |
| remove | GET | `https://www.discogs.com/sell/cart/?remove={listingId}` |

List parses HTML lightly for listing ids / prices (`?remove=`, `/sell/item/`, `span.price`).

Capture: `capture/wave4.har`. See `capture/SOURCE.md`.

## Auth

`/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 cart-list-remove/scripts/cart.py list
python3 cart-list-remove/scripts/cart.py list --json
python3 cart-list-remove/scripts/cart.py remove --listing-id 4345527582
python3 cart-list-remove/scripts/cart.py remove --listing-id 4345527582 --confirm
```
