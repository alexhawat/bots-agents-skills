#!/usr/bin/env python3
"""List marketplace sellers for one release (HTML + summary API, 2026-09-05).

Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.http import get_json, get_text  # noqa: E402
from _lib.mp_html import parse_marketplace_rows  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
HTML_TMPL = "https://www.discogs.com/sell/release/{release_id}"
SUMMARY_TMPL = "https://www.discogs.com/api/shop-page-api/market/release/{release_id}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("release_id", type=int, help="Discogs release id")
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    rid = args.release_id

    summary = get_json(SUMMARY_TMPL.format(release_id=rid), auth)
    print("# release market summary")
    print(
        f"  {summary.get('artistName')} — {summary.get('title')} "
        f"({summary.get('format')})"
    )
    print(
        f"  listings={summary.get('listingsCount')} "
        f"range={summary.get('priceRangeMin')}–{summary.get('priceRangeMax')} "
        f"{summary.get('currency')}"
    )
    if summary.get("thumbnailUrl"):
        print(f"  thumb={summary['thumbnailUrl']}")

    html = get_text(
        HTML_TMPL.format(release_id=rid),
        auth,
        headers={"accept": "text/html"},
    )
    rows = parse_marketplace_rows(html)
    print(f"\n# listings ({len(rows)})")
    for i, r in enumerate(rows, 1):
        price = r["price_text"] or (
            f"{r['currency'] or ''}{r['price']}" if r["price"] is not None else "?"
        )
        print(
            f"{i}. {price} — {r['seller']} — {r['title']} — item={r['item_id']}"
        )
        if r["item_url"]:
            print(f"   {r['item_url']}")
        cond = " / ".join(
            x for x in (r.get("media_condition"), r.get("sleeve_condition")) if x
        )
        bits = []
        if r.get("ships_from"):
            bits.append(f"ships={r['ships_from']}")
        if cond:
            bits.append(cond)
        if bits:
            print(f"   {' | '.join(bits)}")


if __name__ == "__main__":
    main()
