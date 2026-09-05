#!/usr/bin/env python3
"""Search Discogs marketplace sell/list HTML (captured 2026-09-05).

Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.http import get_text  # noqa: E402
from _lib.mp_html import parse_marketplace_rows  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
ENDPOINT = "https://www.discogs.com/sell/list"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("q", help="Search query (artist/title text)")
    ap.add_argument("--format", default="Vinyl", dest="format_name")
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--page", type=int, default=1)
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    params = {
        "format": args.format_name,
        "q": args.q,
        "currency": args.currency,
        "page": str(args.page),
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    html = get_text(url, auth, headers={"accept": "text/html"})
    rows = parse_marketplace_rows(html)
    print(
        f"# marketplace-search q={args.q!r} format={args.format_name} "
        f"currency={args.currency} page={args.page} rows={len(rows)}"
    )
    for i, r in enumerate(rows, 1):
        price = r["price_text"] or (
            f"{r['currency'] or ''}{r['price']}" if r["price"] is not None else "?"
        )
        print(
            f"{i}. {r['title']} — {price} — seller={r['seller']} "
            f"— release={r['release_id']} — item={r['item_id']}"
        )
        if r["item_url"]:
            print(f"   {r['item_url']}")
        cond = " / ".join(
            x for x in (r.get("media_condition"), r.get("sleeve_condition")) if x
        )
        extra = []
        if r.get("ships_from"):
            extra.append(f"ships={r['ships_from']}")
        if cond:
            extra.append(cond)
        if extra:
            print(f"   {' | '.join(extra)}")


if __name__ == "__main__":
    main()
