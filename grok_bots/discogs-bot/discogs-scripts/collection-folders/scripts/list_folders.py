#!/usr/bin/env python3
"""List Discogs collection folders and item counts (read-only).

Uses ViewerCollectionListData (same sha as collection-search / collection-export).
Move-between-folders is Wave 4 — not implemented here.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.errors import DiscogsAPIError, DiscogsAuthError, cli_main  # noqa: E402
from _lib.http import graphql_get  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
GRAPHQL = "https://www.discogs.com/service/catalog/api/graphql"
LIST_SHA = "ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b"


def fetch_folders(auth: dict[str, str], currency: str = "EUR") -> tuple[list[dict], int | None]:
    data = graphql_get(
        auth,
        endpoint=GRAPHQL,
        operation_name="ViewerCollectionListData",
        sha256_hash=LIST_SHA,
        variables={
            "page": 1,
            "perPage": 1,
            "currency": currency,
            "folderId": 0,
            "direction": "DESC",
            "field": "ADDED",
            "search": "",
        },
    )
    viewer = (data.get("data") or {}).get("viewer")
    if viewer is None:
        raise DiscogsAuthError(
            "viewer=null — session dead or COOKIE incomplete. "
            "Run auth-refresh/scripts/refresh.py --check-only"
        )
    if data.get("errors"):
        raise DiscogsAPIError(f"GraphQL errors: {data['errors']!r}")

    folders: list[dict] = []
    for edge in ((viewer.get("collectionFolders") or {}).get("edges") or []):
        node = edge.get("node") or {}
        folders.append(
            {
                "discogsId": node.get("discogsId"),
                "name": node.get("name"),
                "totalCount": node.get("totalCount"),
            }
        )

    total = None
    tc = viewer.get("totalCollectionCount")
    if isinstance(tc, dict):
        total = tc.get("totalCount")
    elif isinstance(tc, int):
        total = tc
    if total is None:
        total = (viewer.get("offsetCollectionItems") or {}).get("totalCount")
    return folders, total


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    folders, total = fetch_folders(auth, currency=args.currency)

    if args.json:
        print(
            json.dumps(
                {"totalCollectionCount": total, "folders": folders},
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    print(f"# totalCollectionCount={total}")
    print(f"{'id':>10}  {'count':>6}  name")
    for f in folders:
        print(f"{f['discogsId']:>10}  {f['totalCount']:>6}  {f['name']}")
    print("# note: move item between folders = Wave 4 / confirm later (not implemented)")


if __name__ == "__main__":
    cli_main(main)
