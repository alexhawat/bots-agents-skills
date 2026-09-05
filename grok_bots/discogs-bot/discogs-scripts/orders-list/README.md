# orders-list / order-status

Wave 5 — buyer purchases list + single-order status (read-only HTML).

## Endpoints

| Subcommand | Method | URL |
|------------|--------|-----|
| `list` | GET | `https://www.discogs.com/sell/purchases` (`?page=N` when `--page` > 1) |
| `status` | GET | `https://www.discogs.com/sell/order/{ORDER_ID}` |

No GraphQL for orders — parse HTML. Capture: `capture/curls.txt`, `capture/SOURCE.md`.

## Auth

`/home/box/discogs-auth/auth.env` via `_lib/auth.py` + `_lib/http.get_text`. Never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 orders-list/scripts/orders.py list
python3 orders-list/scripts/orders.py list --page 1 --json
python3 orders-list/scripts/orders.py status --order-id 1106613-4781
python3 orders-list/scripts/orders.py status --order-id 1106613-4781 --json
# alias:
python3 orders-list/scripts/orders.py order-status --order-id 1106613-4781
```

`list` prints a table: order id, date, seller, total, status.  
`status` prints status, seller, created/last activity, items (id/title/price/conditions), subtotal/shipping/total.
