#!/usr/bin/env python3
"""Lookup Discogs releases by catalog number or barcode.

Uses site autocomplete (captured) + public database/search fallback.
Optional --check-collection via UserReleaseData GraphQL.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.discogs_search import (  # noqa: E402
    SearchHit,
    check_in_collection,
    looks_like_barcode,
    lookup_query,
)
from _lib.errors import DiscogsError, cli_main  # noqa: E402

TASK = Path(__file__).resolve().parents[1]


def format_hit(h: SearchHit, idx: int) -> str:
    artists = h.artists or "?"
    year = h.year or "?"
    extra = []
    if h.catno:
        extra.append(f"catno={h.catno}")
    if h.country:
        extra.append(h.country)
    if h.formats:
        extra.append(h.formats)
    extra.append(f"via={h.source}")
    tail = f"  ({'; '.join(extra)})" if extra else ""
    return (
        f"{idx}. [{h.kind}] id={h.discogs_id}  {artists} — {h.title}  "
        f"({year})\n   {h.url}{tail}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "query",
        nargs="?",
        help="Catalog number or barcode (auto-detected)",
    )
    ap.add_argument("--barcode", help="Force barcode search")
    ap.add_argument("--catno", help="Force catalog-number search")
    ap.add_argument(
        "--check-collection",
        action="store_true",
        help="For each Release hit, call UserReleaseData and note ownership",
    )
    ap.add_argument("--currency", default="EUR")
    ap.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max hits to print (default 20)",
    )
    args = ap.parse_args()

    if args.barcode:
        q = args.barcode.strip()
        as_barcode, as_catno = True, False
    elif args.catno:
        q = args.catno.strip()
        as_barcode, as_catno = False, True
    elif args.query:
        q = args.query.strip()
        as_barcode = looks_like_barcode(q)
        as_catno = not as_barcode
    else:
        ap.error("Provide QUERY, --barcode, or --catno")

    auth = None
    if args.check_collection:
        auth = load_auth(task_root=TASK)
    else:
        # Autocomplete works without Cookie; still load if jar present for richer session
        try:
            auth = load_auth(task_root=TASK)
        except DiscogsError:
            auth = None

    hits = lookup_query(
        q,
        auth,
        as_barcode=as_barcode,
        as_catno=as_catno,
        currency=args.currency,
    )
    if not hits:
        print(f"No matches for {q!r}")
        raise SystemExit(1)

    mode = "barcode" if as_barcode else ("catno" if as_catno else "auto")
    print(f"# barcode-or-catno-lookup  query={q!r}  mode={mode}  hits={len(hits)}")
    shown = hits[: max(1, args.limit)]
    for i, h in enumerate(shown, 1):
        print(format_hit(h, i))
        if args.check_collection and h.is_release and auth:
            info = check_in_collection(auth, h.discogs_id)
            if info["viewer_null"] and not info["in_collection"]:
                print("   in-collection: unknown (viewer=null — session may be stale)")
            elif info["in_collection"]:
                print(f"   in-collection: YES  copies={info['copies']}")
            else:
                print("   in-collection: no")
            want = info.get("in_wantlist")
            if want is not None:
                print(f"   inWantlist={'yes' if want else 'no'}")


if __name__ == "__main__":
    cli_main(main)
