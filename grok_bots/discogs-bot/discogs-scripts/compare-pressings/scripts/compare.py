#!/usr/bin/env python3
"""Compare pressings of a master: list versions and whether each is in your collection.

Resolves --release-id → master_id via public API; checks ownership with
check_in_collection (UserReleaseData). Caps checks with --limit (default 30).
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.discogs_search import PUBLIC_UA, check_in_collection  # noqa: E402
from _lib.errors import DiscogsError, cli_main  # noqa: E402
from _lib.http import get_public_json  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
PUBLIC_RELEASE = "https://api.discogs.com/releases/{id}"
PUBLIC_MASTER = "https://api.discogs.com/masters/{id}"
PUBLIC_VERSIONS = "https://api.discogs.com/masters/{id}/versions"


def resolve_master_id(release_id: int) -> int:
    public = get_public_json(
        PUBLIC_RELEASE.format(id=release_id), user_agent=PUBLIC_UA
    )
    mid = public.get("master_id")
    if not mid:
        raise DiscogsError(f"Release {release_id} has no master_id")
    return int(mid)


def fetch_versions(master_id: int, limit: int, per_page: int = 50) -> list[dict]:
    page = 1
    out: list[dict] = []
    while len(out) < limit:
        url = (
            PUBLIC_VERSIONS.format(id=master_id)
            + "?"
            + urlencode({"page": page, "per_page": min(per_page, limit - len(out))})
        )
        data = get_public_json(url, user_agent=PUBLIC_UA)
        batch = data.get("versions") or []
        if not batch:
            break
        out.extend(batch)
        pag = data.get("pagination") or {}
        pages = int(pag.get("pages") or 1)
        if page >= pages:
            break
        page += 1
        if page > 200:
            break
    return out[:limit]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--release-id", type=int)
    g.add_argument("--master-id", type=int)
    ap.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Max versions to check in collection (default 30)",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.35,
        help="Seconds between UserReleaseData checks (default 0.35)",
    )
    args = ap.parse_args()

    auth = load_auth(task_root=TASK)

    if args.release_id:
        master_id = resolve_master_id(args.release_id)
        highlight = args.release_id
    else:
        master_id = args.master_id
        highlight = None

    master = get_public_json(PUBLIC_MASTER.format(id=master_id), user_agent=PUBLIC_UA)
    # Get total version count from first page pagination
    first = get_public_json(
        PUBLIC_VERSIONS.format(id=master_id) + "?page=1&per_page=1",
        user_agent=PUBLIC_UA,
    )
    total_versions = (first.get("pagination") or {}).get("items")
    versions = fetch_versions(master_id, limit=args.limit)

    print(
        f"# master id={master_id} title={master.get('title')!r} "
        f"year={master.get('year')} versions_total={total_versions} "
        f"checking={len(versions)}"
    )
    if highlight:
        print(f"# highlight release_id={highlight}")

    hdr = (
        f"{'mark':4} {'release_id':>10}  {'in_coll':7}  {'year':4}  "
        f"{'country':12}  {'catno':16}  format"
    )
    print(hdr)
    owned = 0
    for i, v in enumerate(versions):
        vid = int(v.get("id") or 0)
        mark = ">>" if highlight and vid == highlight else "  "
        try:
            coll = check_in_collection(auth, vid)
            in_coll = "yes" if coll.get("in_collection") else "no"
            if coll.get("viewer_null") and not coll.get("in_collection"):
                in_coll = "?"
            if coll.get("in_collection"):
                owned += 1
                copies = coll.get("copies")
                if isinstance(copies, int) and copies > 1:
                    in_coll = f"yes×{copies}"
        except DiscogsError as e:
            in_coll = "err"
            print(f"# check failed for {vid}: {e}", file=sys.stderr)

        year = str(v.get("released") or "")[:4]
        country = (v.get("country") or "")[:12]
        catno = (v.get("catno") or "")[:16]
        fmt = v.get("format") or ""
        print(
            f"{mark:4} {vid:>10}  {in_coll:7}  {year:4}  "
            f"{country:12}  {catno:16}  {fmt}"
        )
        if i + 1 < len(versions) and args.sleep > 0:
            time.sleep(args.sleep)

    print(f"# owned among checked: {owned}/{len(versions)}")


if __name__ == "__main__":
    cli_main(main)
