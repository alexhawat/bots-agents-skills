#!/usr/bin/env python3
"""Search the signed-in Discogs collection (ViewerCollectionListData, captured 2026-09-05).

Fetching, auth and row normalization live in `_lib` — this script is the CLI
and the offline `--from-har` replay path. Never prints secrets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.collection_fetch import artist_blob, format_blob, iter_collection_items  # noqa: E402
from _lib.errors import DiscogsAPIError, cli_main  # noqa: E402

TASK = Path(__file__).resolve().parents[1]


def is_vinyl(release: dict) -> bool:
    for fmt in release.get("formats") or []:
        if (fmt.get("name") or "").lower() == "vinyl":
            return True
    return False


def load_from_har(har_path: Path) -> list[dict]:
    """Offline: pull ViewerCollectionListData payloads out of a captured HAR."""
    har = json.loads(har_path.read_text())
    items: list[dict] = []
    for e in har.get("log", {}).get("entries", []):
        if "ViewerCollectionListData" not in (e.get("request", {}).get("url") or ""):
            continue
        raw = e.get("response", {}).get("content", {}).get("text")
        if not raw:
            continue
        data = json.loads(raw)
        viewer = (data.get("data") or {}).get("viewer") or {}
        off = viewer.get("offsetCollectionItems") or {}
        batch = off.get("collectionItems") or []
        items.extend(batch)
        print(
            f"# from-har totalCount={off.get('totalCount')} items+={len(batch)}",
            file=sys.stderr,
        )
    if not items:
        raise DiscogsAPIError(f"No ViewerCollectionListData payloads in {har_path}")
    return items


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("search", help="Collection search string")
    ap.add_argument("--vinyl-only", action="store_true")
    ap.add_argument(
        "--artist-match",
        metavar="SUBSTR",
        help="Keep rows whose primary artist text contains SUBSTR (case-insensitive)",
    )
    ap.add_argument("--json", action="store_true", help="Print JSON array")
    ap.add_argument("--auth", type=Path, help="Override auth.env path")
    ap.add_argument("--per-page", type=int, default=50)
    ap.add_argument(
        "--from-har",
        type=Path,
        help="Offline: parse ViewerCollectionListData from a HAR (no network)",
    )
    args = ap.parse_args()

    if args.from_har:
        items = load_from_har(args.from_har)
    else:
        auth = load_auth(task_root=TASK, override=args.auth)
        items = list(
            iter_collection_items(
                auth, per_page=args.per_page, search=args.search
            )
        )

    rows = []
    for it in items:
        rel = it.get("release") or {}
        if args.vinyl_only and not is_vinyl(rel):
            continue
        if args.artist_match and args.artist_match.lower() not in artist_blob(rel).lower():
            continue
        discogs_id = rel.get("discogsId")
        site = rel.get("siteUrl") or f"/release/{discogs_id}"
        if site.startswith("/"):
            site = "https://www.discogs.com" + site
        rows.append(
            {
                "collection_item_id": it.get("discogsId"),
                "folder": (it.get("folder") or {}).get("name"),
                "added_at": it.get("addedAt"),
                "release_id": discogs_id,
                "title": rel.get("title"),
                "artists": artist_blob(rel),
                "year": rel.get("released"),
                "format": format_blob(rel),
                "url": site,
            }
        )

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    # Dedupe display by release_id with copy counts
    counts: dict[int, int] = {}
    order: list[dict] = []
    for r in rows:
        rid = r["release_id"]
        counts[rid] = counts.get(rid, 0) + 1
        if counts[rid] == 1:
            order.append(r)
    print(f"{len(rows)} rows, {len(order)} unique releases\n")
    for i, r in enumerate(order, 1):
        n = counts[r["release_id"]]
        copies = f" (×{n})" if n > 1 else ""
        print(
            f"{i}. {r['title']} — {r['artists']} — {r['year'] or '?'} — {r['format']}{copies}"
        )
        print(f"   {r['url']}")


if __name__ == "__main__":
    cli_main(main)
