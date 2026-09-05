#!/usr/bin/env python3
"""Show a master release summary and its versions; highlight a given release.

Input: --release-id (resolve master_id via public GET /releases/{id}) or --master-id.
Optional session GraphQL DeferredReleaseData for masterRelease hint.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.discogs_search import PUBLIC_UA  # noqa: E402
from _lib.errors import DiscogsError, cli_main  # noqa: E402
from _lib.http import get_public_json, graphql_get  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
GRAPHQL = "https://www.discogs.com/service/catalog/api/graphql"
DEFERRED_SHA = "520dd540372aa4c107da14d51139205bc41844c2f442ae134c8cef8c3cff7220"
PUBLIC_RELEASE = "https://api.discogs.com/releases/{id}"
PUBLIC_MASTER = "https://api.discogs.com/masters/{id}"
PUBLIC_VERSIONS = "https://api.discogs.com/masters/{id}/versions"


def resolve_master_id(release_id: int, auth: dict | None) -> tuple[int, dict]:
    """Return (master_id, public_release_json)."""
    public = get_public_json(
        PUBLIC_RELEASE.format(id=release_id), user_agent=PUBLIC_UA
    )
    mid = public.get("master_id")
    if mid:
        return int(mid), public

    # Optional GraphQL fallback for masterRelease
    if auth and auth.get("COOKIE"):
        try:
            gql = graphql_get(
                auth,
                endpoint=GRAPHQL,
                operation_name="DeferredReleaseData",
                sha256_hash=DEFERRED_SHA,
                variables={"discogsId": int(release_id)},
            )
            mr = ((gql.get("data") or {}).get("release") or {}).get("masterRelease")
            if mr and mr.get("discogsId"):
                return int(mr["discogsId"]), public
        except DiscogsError as e:
            print(f"# DeferredReleaseData skipped: {e}", file=sys.stderr)

    raise DiscogsError(
        f"Release {release_id} has no master_id (standalone release / not linked)"
    )


def fetch_all_versions(master_id: int, per_page: int = 100) -> list[dict]:
    page = 1
    out: list[dict] = []
    while True:
        url = (
            PUBLIC_VERSIONS.format(id=master_id)
            + "?"
            + urlencode({"page": page, "per_page": per_page})
        )
        data = get_public_json(url, user_agent=PUBLIC_UA)
        batch = data.get("versions") or []
        out.extend(batch)
        pag = data.get("pagination") or {}
        pages = int(pag.get("pages") or 1)
        if page >= pages or not batch:
            break
        page += 1
        if page > 200:
            break
    return out


def artist_blob(artists: list | None) -> str:
    parts = []
    for a in artists or []:
        name = a.get("name") or ""
        if name:
            parts.append(name)
    return " / ".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--release-id", type=int)
    g.add_argument("--master-id", type=int)
    args = ap.parse_args()

    auth = None
    try:
        auth = load_auth(task_root=TASK)
    except DiscogsError:
        auth = None

    highlight_id: int | None = None
    release_public: dict | None = None
    if args.release_id:
        highlight_id = args.release_id
        master_id, release_public = resolve_master_id(args.release_id, auth)
    else:
        master_id = args.master_id

    master = get_public_json(PUBLIC_MASTER.format(id=master_id), user_agent=PUBLIC_UA)
    versions = fetch_all_versions(master_id)

    print("# master")
    print(f"  id:      {master.get('id')}")
    print(f"  title:   {master.get('title')}")
    print(f"  artists: {artist_blob(master.get('artists'))}")
    print(f"  year:    {master.get('year')}")
    print(f"  genres:  {', '.join(master.get('genres') or [])}")
    print(f"  styles:  {', '.join(master.get('styles') or [])}")
    print(f"  versions:{len(versions)} (api main_release={master.get('main_release')})")
    if release_public:
        print(
            f"# from release {highlight_id}: "
            f"{release_public.get('title')} "
            f"({release_public.get('country')}, {release_public.get('year')})"
        )

    print("\n# versions")
    print(
        f"{'mark':4} {'id':>10}  {'year':4}  {'country':12}  {'catno':16}  format"
    )
    for v in versions:
        vid = v.get("id")
        mark = ">>" if highlight_id and vid == highlight_id else "  "
        year = str(v.get("released") or "")[:4]
        country = (v.get("country") or "")[:12]
        catno = (v.get("catno") or "")[:16]
        fmt = v.get("format") or ""
        print(f"{mark:4} {vid:>10}  {year:4}  {country:12}  {catno:16}  {fmt}")
        if mark.strip():
            print(f"       title={v.get('title')}")


if __name__ == "__main__":
    cli_main(main)
