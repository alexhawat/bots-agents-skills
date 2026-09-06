#!/usr/bin/env python3
"""Export Discogs collection via ViewerCollectionListData (captured 2026-09-05).

Writes CSV + JSON under collection-export/out/. Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.collection_fetch import (  # noqa: E402
    CSV_COLUMNS,
    fetch_rows,
    public_row,
)
from _lib.errors import cli_main  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
OUT = TASK / "out"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--folder-id", type=int, default=0, help="0 = all folders")
    ap.add_argument("--search", default="", help="Collection searchParam (empty = full dump)")
    ap.add_argument("--limit", type=int, default=None, help="Stop after N items")
    ap.add_argument("--per-page", type=int, default=50)
    ap.add_argument("--currency", default="EUR")
    ap.add_argument(
        "--out-prefix",
        default=None,
        help="Basename under out/ (default: collection-YYYYMMDD-HHMMSS)",
    )
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    rows_raw = fetch_rows(
        auth,
        per_page=args.per_page,
        folder_id=args.folder_id,
        search=args.search,
        currency=args.currency,
        limit=args.limit,
    )
    rows = [public_row(r) for r in rows_raw]

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    prefix = args.out_prefix or f"collection-{stamp}"
    csv_path = OUT / f"{prefix}.csv"
    json_path = OUT / f"{prefix}.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    json_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"# wrote {len(rows)} rows")
    print(f"# csv={csv_path}")
    print(f"# json={json_path}")
    for i, r in enumerate(rows[:5], 1):
        print(
            f"{i}. [{r['release_id']}] {r['title']} — {r['artists']} — "
            f"{r['year']} — {r['format']} — {r['label']} {r['catno']}"
        )
        print(f"   folder={r['folder']} added={r['added_at']}")
        print(f"   {r['url']}")


if __name__ == "__main__":
    cli_main(main)
