#!/usr/bin/env python3
"""Print signed-in Discogs identity, folder counts, and optional collection value stats.

Uses captured GraphQL: UserCollectionPageData, ViewerCollectionListData,
ViewerCollectionPageData (value stats — skipped if the query fails).
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import get_username, load_auth  # noqa: E402
from _lib.errors import DiscogsAPIError, DiscogsAuthError, DiscogsError, cli_main  # noqa: E402
from _lib.http import graphql_get  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
GRAPHQL = "https://www.discogs.com/service/catalog/api/graphql"

USER_PAGE_SHA = "4ec9e7cf35dfd68831890df31e7c2d9c32a9d13274db0aaebfd49f7f0331cd96"
LIST_SHA = "ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b"
PAGE_STATS_SHA = "462fbd5e05a757bc5dde79635e33691c036119aea912c7d51c65e81154e4a2b7"


def _money(price: dict | None) -> str:
    if not price:
        return "?"
    converted = price.get("converted") or {}
    if converted.get("amount") is not None:
        return f"{converted['amount']:.2f} {converted.get('currency') or ''}".strip()
    if price.get("amount") is not None:
        return f"{price['amount']:.2f} {price.get('currency') or ''}".strip()
    return "?"


def fetch_profile(auth: dict[str, str], username: str) -> dict:
    data = graphql_get(
        auth,
        endpoint=GRAPHQL,
        operation_name="UserCollectionPageData",
        sha256_hash=USER_PAGE_SHA,
        variables={"username": username},
    )
    if data.get("errors"):
        raise DiscogsAPIError(f"GraphQL errors (UserCollectionPageData): {data['errors']!r}")
    user = (data.get("data") or {}).get("user")
    if not user:
        raise DiscogsAuthError(f"user=null for username={username!r} — check spelling / session")
    return user


def fetch_folders_and_total(
    auth: dict[str, str], currency: str = "EUR"
) -> tuple[list[dict], int | None]:
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
        raise DiscogsAPIError(f"GraphQL errors (ViewerCollectionListData): {data['errors']!r}")

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
        off = viewer.get("offsetCollectionItems") or {}
        total = off.get("totalCount")
    return folders, total


def fetch_value_stats(auth: dict[str, str], currency: str = "EUR") -> dict | None:
    """ViewerCollectionPageData — return collectionStats or None if query fails."""
    try:
        data = graphql_get(
            auth,
            endpoint=GRAPHQL,
            operation_name="ViewerCollectionPageData",
            sha256_hash=PAGE_STATS_SHA,
            variables={"currency": currency, "search": ""},
        )
    except DiscogsError as e:
        print(f"# value stats skipped: {e}", file=sys.stderr)
        return None
    if data.get("errors"):
        print(
            f"# value stats skipped (GraphQL errors): {data['errors']!r}",
            file=sys.stderr,
        )
        return None
    viewer = (data.get("data") or {}).get("viewer")
    if not viewer:
        print("# value stats skipped: viewer=null", file=sys.stderr)
        return None
    return viewer.get("collectionStats")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--username",
        default=None,
        help="Profile username for UserCollectionPageData "
        "(default: USERNAME from load_auth / personal.env)",
    )
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--json", action="store_true", help="Machine-readable JSON")
    ap.add_argument(
        "--skip-value",
        action="store_true",
        help="Do not call ViewerCollectionPageData",
    )
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)
    username = args.username or get_username(auth)

    user = fetch_profile(auth, username)
    folders, total = fetch_folders_and_total(auth, currency=args.currency)
    stats = None if args.skip_value else fetch_value_stats(auth, currency=args.currency)

    out = {
        "username": user.get("username"),
        "discogsId": user.get("discogsId"),
        "avatarUrl": user.get("avatarUrl"),
        "collectionPrivacy": user.get("collectionPrivacy"),
        "wantlistPrivacy": user.get("wantlistPrivacy"),
        "isViewer": user.get("isViewer"),
        "totalCollectionCount": total,
        "folders": folders,
        "collectionStats": None,
    }
    if stats:
        out["collectionStats"] = {
            "min": _money(stats.get("minValue")),
            "median": _money(stats.get("medianValue")),
            "max": _money(stats.get("maxValue")),
            "raw": {
                "minValue": stats.get("minValue"),
                "medianValue": stats.get("medianValue"),
                "maxValue": stats.get("maxValue"),
            },
        }

    if args.json:
        # Drop bulky raw for --json top-level cleanliness; keep amounts
        printable = dict(out)
        if printable.get("collectionStats") and "raw" in printable["collectionStats"]:
            printable["collectionStats"] = {
                k: v
                for k, v in printable["collectionStats"].items()
                if k != "raw"
            }
        print(json.dumps(printable, indent=2, ensure_ascii=False))
        return

    print(f"username:  {out['username']}")
    print(f"discogsId: {out['discogsId']}")
    print(f"isViewer:  {out['isViewer']}")
    print(f"privacy:   collection={out['collectionPrivacy']} wantlist={out['wantlistPrivacy']}")
    if out.get("avatarUrl"):
        print(f"avatar:    {out['avatarUrl']}")
    print(f"total items: {out['totalCollectionCount']}")
    print("folders:")
    for f in folders:
        print(f"  [{f['discogsId']}] {f['name']}: {f['totalCount']}")
    if out.get("collectionStats"):
        cs = out["collectionStats"]
        print("collection value (ViewerCollectionPageData, search=\"\"):")
        print(f"  min:    {cs['min']}")
        print(f"  median: {cs['median']}")
        print(f"  max:    {cs['max']}")
    elif not args.skip_value:
        print("collection value: (unavailable — see stderr / capture/SOURCE.md)")


if __name__ == "__main__":
    cli_main(main)
