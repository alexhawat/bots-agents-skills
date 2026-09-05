#!/usr/bin/env python3
"""Buyer purchases list + order status (HTML, read-only).

Captured 2026-09-05:
  list:   GET https://www.discogs.com/sell/purchases[?page=N]
  status: GET https://www.discogs.com/sell/order/{ORDER_ID}

No GraphQL for orders — parse HTML. Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.http import get_text  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
PURCHASES_URL = "https://www.discogs.com/sell/purchases"
ORDER_URL = "https://www.discogs.com/sell/order/{order_id}"

_TAG_RE = re.compile(r"<[^>]+>")
_ROW_RE = re.compile(
    r'<tr class="[^"]*shortcut_navigable"[^>]*>(.*?)</tr>',
    re.IGNORECASE | re.DOTALL,
)
_ORDER_ID_RE = re.compile(
    r'data-order-id(?:=["\']?|/sell/order/)([0-9]+-[0-9]+)',
    re.IGNORECASE,
)
_ORDER_LINK_RE = re.compile(
    r'href="[^"]*/sell/order/([0-9]+-[0-9]+)"[^>]*>\s*([0-9]+-[0-9]+)\s*<',
    re.IGNORECASE,
)
_SELLER_RE = re.compile(
    r'data-header="Seller:\s*"[^>]*>.*?class="user"[^>]*>([^<]+)<',
    re.IGNORECASE | re.DOTALL,
)
_TOTAL_RE = re.compile(
    r'data-header="Total:\s*"[^>]*>.*?<span class="price">([^<]*)</span>',
    re.IGNORECASE | re.DOTALL,
)
_DATE_RE = re.compile(
    r'data-header="Date:\s*"[^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
_STATUS_CELL_RE = re.compile(
    r'class="[^"]*order_status_cell[^"]*"[^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL,
)
_STATUS_ARIA_RE = re.compile(
    r'aria-label="([^"]+)"',
    re.IGNORECASE,
)
_ITEM_ROW_RE = re.compile(
    r'<tr[^>]*class="[^"]*order-item-row"[^>]*'
    r'data-id="(\d+)"[^>]*'
    r'data-title="([^"]*)"[^>]*'
    r'data-price="([^"]*)"[^>]*>'
    r'(.*?)</tr>',
    re.IGNORECASE | re.DOTALL,
)
_RELEASE_LINK_RE = re.compile(
    r'class="order-item-info"[^>]*>\s*<a[^>]*href="(/release/[^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_MEDIA_COND_RE = re.compile(
    r"Media\s*(?:<span[^>]*>Condition</span>)?\s*:\s*"
    r'(?:<span[^>]*>\s*)?([^<\n]+)',
    re.IGNORECASE,
)
_SLEEVE_COND_RE = re.compile(
    r"Sleeve\s*(?:<span[^>]*>Condition</span>)?\s*:\s*"
    r'<span[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_PRICE_TEXT_RE = re.compile(
    r'<td class="textright monospace_font[^"]*"[^>]*>\s*([^<]+?)\s*</td>',
    re.IGNORECASE,
)
_STATUS_LABEL_RE = re.compile(
    r'<(?:span|div)([^>]*order-status-label[^>]*)>(.*?)</(?:span|div)>',
    re.IGNORECASE | re.DOTALL,
)
_ATTR_TITLE_RE = re.compile(
    r'data-original-title="([^"]*)"',
    re.IGNORECASE,
)
_TIMESTAMP_RE = re.compile(
    r'<span class="order-timestamp">\s*<strong>([^<]+)</strong>\s*:\s*([^<]+?)\s*</span>',
    re.IGNORECASE,
)
_SUBTOTAL_RE = re.compile(
    r'class="[^"]*order_label[^"]*"[^>]*>\s*Subtotal[^<]*</td>\s*'
    r'<td[^>]*>\s*([^<]+?)\s*</td>',
    re.IGNORECASE | re.DOTALL,
)
_SHIPPING_RE = re.compile(
    r'class="[^"]*order_label[^"]*"[^>]*>\s*Shipping\s*(?:\(([^)]*)\))?\s*</td>\s*'
    r'<td[^>]*>\s*([^<]+?)\s*</td>',
    re.IGNORECASE | re.DOTALL,
)
_ORDER_TOTAL_RE = re.compile(
    r'<strong>\s*Total\s*</strong>\s*</td>\s*'
    r'<td[^>]*>\s*(?:<span class=price>)?([^<\n]+)',
    re.IGNORECASE | re.DOTALL,
)
_SELLER_ASIDE_RE = re.compile(
    r'class="order-user-details"[^>]*>.*?<a[^>]*>([^<]+)</a>',
    re.IGNORECASE | re.DOTALL,
)
_HEADING_ID_RE = re.compile(
    r'class="order-page-heading"[^>]*>\s*Order\s*#([0-9]+-[0-9]+)',
    re.IGNORECASE,
)


def _strip(s: str) -> str:
    return html_mod.unescape(_TAG_RE.sub("", s)).strip()


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse_purchases(html: str) -> list[dict[str, Any]]:
    """Parse buyer purchases table rows."""
    orders: list[dict[str, Any]] = []
    seen: set[str] = set()

    for m in _ROW_RE.finditer(html):
        body = m.group(0)
        if "data-order-id" not in body and "/sell/order/" not in body:
            continue
        oid = None
        om = _ORDER_ID_RE.search(body)
        if om:
            oid = om.group(1)
        if not oid:
            lm = _ORDER_LINK_RE.search(body)
            if lm:
                oid = lm.group(1)
        if not oid or oid in seen:
            continue
        seen.add(oid)

        seller = None
        sm = _SELLER_RE.search(body)
        if sm:
            seller = _strip(sm.group(1))

        total = None
        tm = _TOTAL_RE.search(body)
        if tm:
            total = _collapse(_strip(tm.group(1)))

        date = None
        dm = _DATE_RE.search(body)
        if dm:
            date = _collapse(_strip(dm.group(1)))

        status = None
        scm = _STATUS_CELL_RE.search(body)
        if scm:
            cell = scm.group(1)
            am = _STATUS_ARIA_RE.search(cell)
            if am:
                status = _collapse(am.group(1))
            else:
                status = _collapse(_strip(cell))
        if not status:
            # mobile wrap fallback
            am = _STATUS_ARIA_RE.search(body)
            if am:
                status = _collapse(am.group(1))

        orders.append(
            {
                "order_id": oid,
                "date": date,
                "seller": seller,
                "status": status,
                "total": total,
            }
        )
    return orders


def parse_order_detail(html: str, order_id: str) -> dict[str, Any]:
    """Parse a single buyer order page."""
    status = None
    sm = _STATUS_LABEL_RE.search(html)
    if sm:
        attrs, inner = sm.group(1), sm.group(2)
        title_m = _ATTR_TITLE_RE.search(attrs)
        short = _collapse(_strip(inner))
        full = _collapse(title_m.group(1)) if title_m else None
        # Prefer full tooltip/title when longer than short badge text
        if full and (not short or len(full) >= len(short)):
            status = full
        else:
            status = short or full

    dates: dict[str, str] = {}
    for tm in _TIMESTAMP_RE.finditer(html):
        key = _collapse(tm.group(1)).lower().replace(" ", "_")
        dates[key] = _collapse(tm.group(2))

    seller = None
    sem = _SELLER_ASIDE_RE.search(html)
    if sem:
        seller = _strip(sem.group(1))

    items: list[dict[str, Any]] = []
    for im in _ITEM_ROW_RE.finditer(html):
        item_id = im.group(1)
        data_title = html_mod.unescape(im.group(2))
        data_price = im.group(3)
        row = im.group(0)
        title = data_title
        release_url = None
        rm = _RELEASE_LINK_RE.search(row)
        if rm:
            release_url = rm.group(1)
            if release_url.startswith("/"):
                release_url = "https://www.discogs.com" + release_url
            title = _collapse(_strip(rm.group(2))) or data_title

        media = None
        mm = _MEDIA_COND_RE.search(row)
        if mm:
            media = _collapse(_strip(mm.group(1)))
        sleeve = None
        slm = _SLEEVE_COND_RE.search(row)
        if slm:
            sleeve = _collapse(_strip(slm.group(1)))

        price_text = None
        pm = _PRICE_TEXT_RE.search(row)
        if pm:
            price_text = _collapse(_strip(pm.group(1)))

        items.append(
            {
                "item_id": int(item_id),
                "title": title,
                "price": price_text,
                "price_value": data_price,
                "release_url": release_url,
                "media_condition": media,
                "sleeve_condition": sleeve,
            }
        )

    subtotal = None
    sum_m = _SUBTOTAL_RE.search(html)
    if sum_m:
        subtotal = _collapse(_strip(sum_m.group(1)))

    shipping = None
    shipping_method = None
    ship_m = _SHIPPING_RE.search(html)
    if ship_m:
        shipping_method = _collapse(ship_m.group(1) or "") or None
        shipping = _collapse(_strip(ship_m.group(2)))

    total = None
    tot_m = _ORDER_TOTAL_RE.search(html)
    if tot_m:
        total = _collapse(_strip(tot_m.group(1)))

    heading_id = order_id
    hm = _HEADING_ID_RE.search(html)
    if hm:
        heading_id = hm.group(1)

    return {
        "order_id": heading_id,
        "status": status,
        "seller": seller,
        "dates": dates,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "shipping_method": shipping_method,
        "total": total,
    }


def _fetch_html(url: str) -> str:
    auth = load_auth(task_root=TASK)
    return get_text(
        url,
        auth,
        headers={"accept": "text/html,application/xhtml+xml"},
    )


def cmd_list(page: int, as_json: bool) -> None:
    url = PURCHASES_URL
    if page and page > 1:
        url = f"{PURCHASES_URL}?page={page}"
    html = _fetch_html(url)
    orders = parse_purchases(html)
    if as_json:
        print(
            json.dumps(
                {"page": page, "count": len(orders), "orders": orders},
                indent=2,
                ensure_ascii=False,
            )
        )
        return
    print(f"# purchases page={page} orders={len(orders)}")
    print(f"{'order_id':<16}  {'date':<22}  {'seller':<18}  {'total':>10}  status")
    for o in orders:
        print(
            f"{o['order_id']:<16}  {(o['date'] or '?'):<22}  "
            f"{(o['seller'] or '?'):<18}  {(o['total'] or '?'):>10}  "
            f"{o['status'] or '?'}"
        )


def cmd_status(order_id: str, as_json: bool) -> None:
    if not re.fullmatch(r"[0-9]+-[0-9]+", order_id):
        raise SystemExit(f"Invalid order id format: {order_id!r} (expect NNN-NNN)")
    url = ORDER_URL.format(order_id=order_id)
    html = _fetch_html(url)
    detail = parse_order_detail(html, order_id)
    if as_json:
        print(json.dumps(detail, indent=2, ensure_ascii=False))
        return
    print(f"# order {detail['order_id']} status={detail.get('status') or '?'}")
    if detail.get("seller"):
        print(f"seller: {detail['seller']}")
    for k, v in (detail.get("dates") or {}).items():
        print(f"{k}: {v}")
    print(f"items: {len(detail.get('items') or [])}")
    for it in detail.get("items") or []:
        cond = " / ".join(
            x for x in (it.get("media_condition"), it.get("sleeve_condition")) if x
        )
        print(
            f"  - {it['item_id']}: {it.get('title') or '?'} — {it.get('price') or '?'}"
        )
        if cond:
            print(f"    {cond}")
    if detail.get("subtotal"):
        print(f"subtotal: {detail['subtotal']}")
    if detail.get("shipping"):
        method = detail.get("shipping_method")
        extra = f" ({method})" if method else ""
        print(f"shipping: {detail['shipping']}{extra}")
    if detail.get("total"):
        print(f"total: {detail['total']}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Discogs buyer orders (list / status). Read-only HTML."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List purchases from /sell/purchases")
    p_list.add_argument("--page", type=int, default=1, help="Page number (default 1)")
    p_list.add_argument("--json", action="store_true", help="JSON output")

    p_status = sub.add_parser(
        "status",
        aliases=["order-status"],
        help="Order detail/status from /sell/order/{id}",
    )
    p_status.add_argument("--order-id", required=True, help="Order id e.g. 1106613-4781")
    p_status.add_argument("--json", action="store_true", help="JSON output")

    args = ap.parse_args()
    if args.cmd == "list":
        cmd_list(args.page, args.json)
    elif args.cmd in ("status", "order-status"):
        cmd_status(args.order_id, args.json)
    else:
        ap.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
