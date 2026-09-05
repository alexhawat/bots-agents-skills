#!/usr/bin/env python3
"""Wantlist-for-sale deals under a max buyer price (sell_item API, 2026-09-05).

Uses buyerItemPrice in buyer currency. Paginates until enough matches or feed ends.
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
from _lib.http import get_json  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
ENDPOINT = "https://www.discogs.com/api/shop-page-api/sell_item"


def buyer_price(it: dict[str, Any]) -> float | None:
    price = it.get("price") or {}
    val = price.get("buyerItemPrice")
    if val is None:
        val = price.get("amount")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def format_deal(it: dict[str, Any]) -> str:
    rel = it.get("release") or {}
    artists = " / ".join(
        a.get("name") or "" for a in (rel.get("artists") or []) if a.get("name")
    )
    title = rel.get("title") or "?"
    fmts = ", ".join(rel.get("formatNames") or [])
    price = it.get("price") or {}
    amount = price.get("buyerItemPrice")
    cur = price.get("buyerCurrencyCode") or price.get("currencyCode") or ""
    seller = it.get("seller") or {}
    seller_name = seller.get("username") or seller.get("name") or seller
    if isinstance(seller_name, dict):
        seller_name = seller_name.get("username") or "?"
    return (
        f"{cur}{amount} — {artists} — {title} [{fmts}] — "
        f"{seller_name} — {it.get('mediaCondition')}/{it.get('sleeveCondition')} "
        f"— item={it.get('itemId')} release={rel.get('releaseId')}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-price", type=float, required=True, help="Max buyerItemPrice")
    ap.add_argument("--format-name", default="Vinyl")
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--seller-rating-min", type=int, default=90)
    ap.add_argument("--count", type=int, default=50, help="Page size")
    ap.add_argument("--limit", type=int, default=50, help="Max deals to print")
    ap.add_argument("--ships-from", default=None)
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    deals: list[dict[str, Any]] = []
    offset = 0
    total = None
    pages = 0
    while len(deals) < args.limit:
        params: dict[str, str] = {
            "count": str(args.count),
            "offset": str(offset),
            "sort": "price",
            "sortOrder": "ascending",
            "sellerRatingMin": str(args.seller_rating_min),
            "currency": args.currency,
            "formatName": args.format_name,
            "facets": "true",
        }
        if args.ships_from:
            params["shipsFrom"] = args.ships_from
        data = get_json(f"{ENDPOINT}?{urllib.parse.urlencode(params)}", auth)
        if total is None:
            total = data.get("totalCount")
        items = data.get("items") or []
        pages += 1
        if not items:
            break
        stop_early = False
        for it in items:
            bp = buyer_price(it)
            if bp is None:
                continue
            if bp > args.max_price:
                # sorted ascending by price — rest of feed is more expensive
                stop_early = True
                break
            deals.append(it)
            if len(deals) >= args.limit:
                break
        if stop_early or len(items) < args.count:
            break
        offset += args.count
        if pages > 40:
            break

    print(
        f"# wantlist-vs-marketplace under {args.currency}{args.max_price} "
        f"formatName={args.format_name} feed_total={total} deals={len(deals)} "
        f"pages={pages}"
    )
    for i, it in enumerate(deals, 1):
        print(f"{i}. {format_deal(it)}")


if __name__ == "__main__":
    main()
