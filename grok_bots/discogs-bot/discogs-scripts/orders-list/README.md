# orders-list / order-status

Wave 5 — buyer purchases list + single-order status (read-only HTML).

## Endpoints

| Subcommand | Method | URL |
|------------|--------|-----|
| `list` | GET | `https://www.discogs.com/sell/purchases` (`?page=N` when `--page` > 1) |
| `status` | GET | `https://www.discogs.com/sell/order/{ORDER_ID}` |

No GraphQL for orders — parse HTML. Capture: `capture/curls.txt`, `capture/SOURCE.md`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) via `_lib/auth.py` + `_lib/http.get_text`. Never print Cookie.

## CLI

```bash
cd discogs-scripts
uv run python orders-list/scripts/orders.py list
uv run python orders-list/scripts/orders.py list --page 1 --json
uv run python orders-list/scripts/orders.py status --order-id 1106613-4781
uv run python orders-list/scripts/orders.py status --order-id 1106613-4781 --json
# alias:
uv run python orders-list/scripts/orders.py order-status --order-id 1106613-4781
```

`list` prints a table: order id, date, seller, total, status.  
`status` prints status, seller, created/last activity, items (id/title/price/conditions), subtotal/shipping/total.
