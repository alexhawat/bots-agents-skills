#!/usr/bin/env python3
"""Add a marketplace listing to the Discogs shopping cart.

Captured as navigation GET:
  https://www.discogs.com/sell/cart/?add={listingId}
  (optional &ev=… tracking param omitted; not required)

HARD confirm: requires BOTH --confirm AND --i-really-mean-it.
Without both: dry explain and exit 2.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.errors import ConfirmationRequired, cli_main  # noqa: E402
from _lib.http import get_text  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
CART_ADD = "https://www.discogs.com/sell/cart/?add={listing_id}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--listing-id", type=int, required=True)
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument(
        "--i-really-mean-it",
        action="store_true",
        help="Second hard-confirm flag (required with --confirm)",
    )
    args = ap.parse_args()

    url = CART_ADD.format(listing_id=args.listing_id)
    if not (args.confirm and args.i_really_mean_it):
        print("# planned CART ADD (navigation GET mutate)")
        print(f"# GET {url}")
        print("# hard confirm required: pass BOTH --confirm AND --i-really-mean-it")
        print("# dry-run: refusing to mutate cart (exit 2)")
        raise ConfirmationRequired("")

    auth = load_auth(task_root=TASK)
    html = get_text(url, auth, headers={"accept": "text/html,application/xhtml+xml"})
    # Light success signal — cart page title / remove link for this listing
    marker = f"remove={args.listing_id}"
    if marker in html or "Shopping Cart" in html or "shopping cart" in html.lower():
        print(f"# ok: cart add requested for listing_id={args.listing_id}")
        if marker in html:
            print(f"# page contains remove={args.listing_id}")
        else:
            print("# page loaded; remove= link not spotted (listing may be gone/unavailable)")
    else:
        print(f"# warning: unexpected cart HTML after add listing_id={args.listing_id}")
        print(f"# html_len={len(html)}")


if __name__ == "__main__":
    cli_main(main)
