#!/usr/bin/env python3
"""Find duplicate releases in Discogs collection (count >= 2).

Uses ViewerCollectionListData via _lib/collection_fetch (captured 2026-09-05).
Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.collection_fetch import fetch_rows, public_row  # noqa: E402
from _lib.errors import cli_main  # noqa: E402

TASK = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--folder-id", type=int, default=0)
    ap.add_argument("--search", default="")
    ap.add_argument("--limit", type=int, default=None, help="Cap fetch size (debug)")
    ap.add_argument("--per-page", type=int, default=50)
    ap.add_argument("--min-count", type=int, default=2)
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    rows = fetch_rows(
        auth,
        per_page=args.per_page,
        folder_id=args.folder_id,
        search=args.search,
        limit=args.limit,
    )

    by_rid: dict[int | str, list[dict]] = defaultdict(list)
    for r in rows:
        rid = r.get("release_id")
        if rid is None:
            continue
        by_rid[rid].append(public_row(r))

    dupes = sorted(
        ((rid, items) for rid, items in by_rid.items() if len(items) >= args.min_count),
        key=lambda x: (-len(x[1]), str(x[0])),
    )

    print(
        f"# scanned={len(rows)} unique_releases={len(by_rid)} "
        f"dupes>={args.min_count}: {len(dupes)}"
    )
    for rid, items in dupes:
        head = items[0]
        print(
            f"×{len(items)}  [{rid}] {head['title']} — {head['artists']} — "
            f"{head['year']} — {head['format']}"
        )
        print(f"   {head['url']}")
        for it in items:
            print(
                f"   - item={it['collection_item_id']} folder={it['folder']!r} "
                f"added={it['added_at']}"
            )


if __name__ == "__main__":
    cli_main(main)
