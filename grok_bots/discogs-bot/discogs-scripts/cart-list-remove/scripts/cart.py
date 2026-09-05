#!/usr/bin/env python3
"""List Discogs cart contents (read-only) or remove a listing.

Captured:
  list:   GET https://www.discogs.com/sell/cart/
  remove: GET https://www.discogs.com/sell/cart/?remove={listingId}

list: no confirm. remove: --confirm or dry-run exit 2.
Never prints Cookie / secrets.
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
from _lib.graphql_mutate import require_confirm  # noqa: E402
from _lib.http import get_text  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
CART_URL = "https://www.discogs.com/sell/cart/"

_ITEM_RE = re.compile(r"/sell/item/(\d+)", re.IGNORECASE)
_REMOVE_RE = re.compile(r"[?&]remove=(\d+)", re.IGNORECASE)
_PRICE_RE = re.compile(
    r'<span\s+class="price"([^>]*)>(.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
_ATTR_RE = re.compile(r'([a-zA-Z0-9_-]+)\s*=\s*"([^"]*)"')
_TITLE_RE = re.compile(
    r'<a[^>]*class="[^"]*item_description_title[^"]*"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_ROW_RE = re.compile(
    r"<tr([^>]*)>(.*?)</tr>",
    re.IGNORECASE | re.DOTALL,
)


def _strip(s: str) -> str:
    return html_mod.unescape(_TAG_RE.sub("", s)).strip()


def parse_cart(html: str) -> list[dict[str, Any]]:
    """Light parse: listing ids + prices from cart HTML."""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Prefer table rows that mention remove= or /sell/item/
    for m in _ROW_RE.finditer(html):
        body = m.group(0)
        if "remove=" not in body and "/sell/item/" not in body:
            continue
        lid = None
        rm = _REMOVE_RE.search(body)
        if rm:
            lid = rm.group(1)
        if not lid:
            im = _ITEM_RE.search(body)
            if im:
                lid = im.group(1)
        if not lid or lid in seen:
            continue
        seen.add(lid)

        price = None
        currency = None
        pm = _PRICE_RE.search(body)
        if pm:
            attrs = dict(_ATTR_RE.findall(pm.group(1)))
            currency = attrs.get("data-currency")
            price = attrs.get("data-pricevalue") or _strip(pm.group(2))
        title = None
        tm = _TITLE_RE.search(body)
        if tm:
            title = _strip(tm.group(1))
        items.append(
            {
                "listing_id": int(lid),
                "price": price,
                "currency": currency,
                "title": title,
            }
        )

    # Fallback: any remove= links not caught in rows
    for rm in _REMOVE_RE.finditer(html):
        lid = rm.group(1)
        if lid in seen:
            continue
        seen.add(lid)
        items.append(
            {"listing_id": int(lid), "price": None, "currency": None, "title": None}
        )
    return items


def cmd_list(as_json: bool) -> None:
    auth = load_auth(task_root=TASK)
    html = get_text(
        CART_URL, auth, headers={"accept": "text/html,application/xhtml+xml"}
    )
    items = parse_cart(html)
    if as_json:
        print(json.dumps({"count": len(items), "items": items}, indent=2, ensure_ascii=False))
        return
    print(f"# cart items: {len(items)}")
    print(f"{'listing_id':>12}  {'price':>12}  title")
    for it in items:
        price = it["price"] or "?"
        cur = it["currency"] or ""
        pstr = f"{price} {cur}".strip()
        title = (it["title"] or "")[:60]
        print(f"{it['listing_id']:>12}  {pstr:>12}  {title}")


def cmd_remove(listing_id: int, confirm: bool) -> None:
    url = f"{CART_URL}?remove={listing_id}"
    planned = (
        f"# planned CART REMOVE (navigation GET mutate)\n"
        f"# GET {url}"
    )
    require_confirm(confirm, planned)

    auth = load_auth(task_root=TASK)
    html = get_text(url, auth, headers={"accept": "text/html,application/xhtml+xml"})
    marker = f"remove={listing_id}"
    if marker in html:
        print(f"# warning: remove={listing_id} still present on cart page")
    else:
        print(f"# ok: removed listing_id={listing_id} (or was not in cart)")
    remaining = parse_cart(html)
    print(f"# cart now has {len(remaining)} item(s)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    list_p = sub.add_parser("list", help="List cart (read-only)")
    list_p.add_argument("--json", action="store_true")

    rm_p = sub.add_parser("remove", help="Remove listing from cart")
    rm_p.add_argument("--listing-id", type=int, required=True)
    rm_p.add_argument("--confirm", action="store_true")

    args = ap.parse_args()
    if args.cmd == "list":
        cmd_list(args.json)
    else:
        cmd_remove(args.listing_id, args.confirm)


if __name__ == "__main__":
    main()
