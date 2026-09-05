# Capture notes — orders-list / order-status

- Date: 2026-09-05
- Auth: session Cookie (never logged). HAR/`curls.txt` cookies redacted.
- No GraphQL / XHR for order data — server-rendered HTML navigations only.

## Endpoints

| Action | Method | URL |
|--------|--------|-----|
| Buyer purchases list | GET | `https://www.discogs.com/sell/purchases` (+ `?page=N` if paginated) |
| Order detail / status | GET | `https://www.discogs.com/sell/order/{ORDER_ID}` e.g. `1106613-4781` |

Also observed (unrelated header chrome): `/service/header/public/api/counts`, `/service/header/public/api/knockauth`.

## Purchases list HTML (redacted structure)

```
<table class="table_block … marketplace-table">
  <thead> … Order # | Summary | Seller | Total | Date | Status | Actions …</thead>
  <tr class="odd shortcut_navigable">
    <td><input type="checkbox" data-order-id=NNNN-NNNN …></td>
    <td class="… order_number" data-header="Order:">
      <a href="https://www.discogs.com/sell/order/NNNN-NNNN">NNNN-NNNN</a>
    </td>
    <td class="purchase_release_info">… release links …</td>
    <td data-header="Seller: "><a class="user" href="/user/…">SELLER</a>…</td>
    <td data-header="Total: "><span class="price">…</span></td>
    <td data-header="Date: ">Mon DD, YYYY HH:MM AM/PM</td>
    <td class="… order_status_cell">
      <span class="order_status_icon …"><i aria-label="STATUS TEXT"></i></span>
      STATUS TEXT
    </td>
    <td class="row_actions"><a class="view_order_link" href="…/sell/order/…">View</a>…</td>
  </tr>
</table>
```

Live tune (2026-09-05): 40 rows on page 1 (`data-order-id` unquoted; status via `aria-label` on icon).

## Order detail HTML (redacted structure)

```
<h1 class="order-page-heading">Order #NNNN-NNNN
  <span class="order-status-label …" data-original-title="Full Status">Short</span>
</h1>
<span class="order-timestamp"><strong>Created</strong>: …</span>
<span class="order-timestamp"><strong>Last activity</strong>: …</span>

<tr class="… order-item-row" data-id="ITEM_ID" data-title="…" data-price="N.N">
  <td>ITEM_ID</td>
  <td class="… order_item">
    <div class="order-item-info"><a href="/release/…">Artist - Title (Format)</a>
      <div class="order-item-conditions">Media …: … Sleeve …: …</div>
    </div>
  </td>
  <td class="textright monospace_font">PRICE</td>
</tr>
… Subtotal / Shipping (method) / Total rows (order_label + monospace_font) …
<aside>… order-user-details → seller profile link …</aside>
```

Do not store shipping address / email / phone from detail pages in capture notes.
