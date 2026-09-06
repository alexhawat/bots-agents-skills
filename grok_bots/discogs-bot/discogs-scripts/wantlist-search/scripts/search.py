#!/usr/bin/env python3
"""Search wantlist-for-sale feed (shop-page-api/sell_item, captured 2026-09-05).

Capture surface: /sell/mywants (wantlist items currently listed for sale).
Text search is client-side (API has no q). Do not send fast/wants (422).
Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.errors import cli_main  # noqa: E402
from _lib.http import get_json  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
ENDPOINT = "https://www.discogs.com/api/shop-page-api/sell_item"


def item_blob(it: dict[str, Any]) -> str:
    rel = it.get("release") or {}
    artists = " / ".join(
        a.get("name") or "" for a in (rel.get("artists") or []) if a.get("name")
    )
    title = rel.get("title") or ""
    return f"{artists} {title}".lower()


def format_item(it: dict[str, Any]) -> str:
    rel = it.get("release") or {}
    artists = " / ".join(
        a.get("name") or "" for a in (rel.get("artists") or []) if a.get("name")
    )
    title = rel.get("title") or "?"
    fmts = ", ".join(rel.get("formatNames") or [])
    price = it.get("price") or {}
    amount = price.get("buyerItemPrice")
    if amount is None:
        amount = price.get("amount")
    cur = price.get("buyerCurrencyCode") or price.get("currencyCode") or ""
    seller = (it.get("seller") or {})
    seller_name = seller.get("username") or seller.get("name") or seller
    if isinstance(seller_name, dict):
        seller_name = seller_name.get("username") or "?"
    return (
        f"{artists} — {title} [{fmts}] — {cur}{amount} — "
        f"seller={seller_name} — media={it.get('mediaCondition')} "
        f"sleeve={it.get('sleeveCondition')} — item={it.get('itemId')} "
        f"release={rel.get('releaseId')}"
    )


def fetch_page(auth: dict[str, str], params: dict[str, str]) -> dict[str, Any]:
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    return get_json(url, auth)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("q", nargs="?", default=None, help="Optional client-side text filter")
    ap.add_argument("--q", dest="q_flag", default=None, help="Optional client-side text filter")
    ap.add_argument("--format-name", default="Vinyl")
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--count", type=int, default=25)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--seller-rating-min", type=int, default=90)
    ap.add_argument(
        "--sort",
        default="listedDate",
        choices=("listedDate", "price"),
    )
    ap.add_argument(
        "--sort-order",
        default="descending",
        choices=("ascending", "descending"),
    )
    ap.add_argument("--ships-from", default=None)
    args = ap.parse_args()
    q = args.q_flag if args.q_flag is not None else args.q

    auth = load_auth(task_root=TASK)
    params: dict[str, str] = {
        "count": str(args.count),
        "offset": str(args.offset),
        "sort": args.sort,
        "sortOrder": args.sort_order,
        "sellerRatingMin": str(args.seller_rating_min),
        "currency": args.currency,
        "formatName": args.format_name,
        "facets": "true",
    }
    if args.ships_from:
        params["shipsFrom"] = args.ships_from

    data = fetch_page(auth, params)
    items = data.get("items") or []
    total = data.get("totalCount")
    if q:
        needle = q.lower()
        items = [it for it in items if needle in item_blob(it)]

    print(
        f"# wantlist-for-sale feed totalCount={total} shown={len(items)} "
        f"q={q!r} formatName={args.format_name} currency={args.currency}"
    )
    for i, it in enumerate(items, 1):
        print(f"{i}. {format_item(it)}")
        listed = it.get("listedDate")
        if listed:
            print(f"   listed={listed}")


if __name__ == "__main__":
    cli_main(main)
