#!/usr/bin/env python3
"""Filter collection by label substring, year range, and/or format.

Uses ViewerCollectionListData via _lib/collection_fetch (captured 2026-09-05).
Format matches against format name + description (e.g. Vinyl, LP).
Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.collection_fetch import (  # noqa: E402
    fetch_rows,
    format_match_blob,
    public_row,
    year_int,
)

TASK = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", default=None, help="Substring match on primary label name")
    ap.add_argument("--year", type=int, default=None, help="Exact year (from released)")
    ap.add_argument("--year-min", type=int, default=None)
    ap.add_argument("--year-max", type=int, default=None)
    ap.add_argument(
        "--format",
        dest="format_substr",
        default=None,
        help="Substring on format name/description (e.g. Vinyl)",
    )
    ap.add_argument("--folder-id", type=int, default=0)
    ap.add_argument("--search", default="", help="Server-side collection searchParam")
    ap.add_argument("--limit", type=int, default=None, help="Cap fetch size (debug)")
    ap.add_argument("--per-page", type=int, default=50)
    args = ap.parse_args()

    if not any(
        [
            args.label,
            args.year is not None,
            args.year_min is not None,
            args.year_max is not None,
            args.format_substr,
        ]
    ):
        raise SystemExit(
            "Provide at least one filter: --label, --year/--year-min/--year-max, --format"
        )

    if args.year is not None:
        y_min = y_max = args.year
    else:
        y_min, y_max = args.year_min, args.year_max

    auth = load_auth(task_root=TASK)
    rows = fetch_rows(
        auth,
        per_page=args.per_page,
        folder_id=args.folder_id,
        search=args.search,
        limit=args.limit,
    )

    label_q = (args.label or "").lower()
    fmt_q = (args.format_substr or "").lower()
    matched: list[dict] = []
    for r in rows:
        if label_q and label_q not in (r.get("label") or "").lower():
            continue
        if fmt_q:
            blob = format_match_blob(r.get("_release") or {})
            # also allow the human format string
            blob = blob + " " + (r.get("format") or "").lower()
            if fmt_q not in blob:
                continue
        y = year_int(r.get("year"))
        if y_min is not None or y_max is not None:
            if y is None:
                continue
            if y_min is not None and y < y_min:
                continue
            if y_max is not None and y > y_max:
                continue
        matched.append(public_row(r))

    print(f"# scanned={len(rows)} matched={len(matched)}")
    for i, r in enumerate(matched, 1):
        print(
            f"{i}. [{r['release_id']}] {r['title']} — {r['artists']} — "
            f"{r['year']} — {r['format']} — {r['label']} {r['catno']}"
        )
        print(f"   folder={r['folder']} {r['url']}")


if __name__ == "__main__":
    main()
