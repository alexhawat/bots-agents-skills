#!/usr/bin/env python3
"""Price / ownership stats for a release (market summary + UserReleaseData + public API).

Captured / documented 2026-09-05. Never prints Cookie values.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.errors import cli_main  # noqa: E402
from _lib.http import DEFAULT_UA, get_json, get_public_json  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
SUMMARY_TMPL = "https://www.discogs.com/api/shop-page-api/market/release/{release_id}"
GRAPHQL = "https://www.discogs.com/service/catalog/api/graphql"
USER_RELEASE_SHA = (
    "a5c6a6cf7e06b6a9d43ab71e49f9e0e4ecb0f204d0db43a63d0f279075bd06e4"
)
PUBLIC_TMPL = "https://api.discogs.com/releases/{release_id}"


def fetch_user_release(auth: dict[str, str], release_id: int) -> dict:
    params = {
        "operationName": "UserReleaseData",
        "variables": json.dumps({"discogsId": release_id}, separators=(",", ":")),
        "extensions": json.dumps(
            {"persistedQuery": {"version": 1, "sha256Hash": USER_RELEASE_SHA}},
            separators=(",", ":"),
        ),
    }
    url = f"{GRAPHQL}?{urllib.parse.urlencode(params)}"
    return get_json(url, auth, apollo=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("release_id", type=int)
    args = ap.parse_args()
    rid = args.release_id
    auth = load_auth(task_root=TASK)

    summary = get_json(SUMMARY_TMPL.format(release_id=rid), auth)
    print("# market summary (shop-page-api)")
    print(f"  artist: {summary.get('artistName')}")
    print(f"  title:  {summary.get('title')}")
    print(f"  format: {summary.get('format')}")
    print(
        f"  listings: {summary.get('listingsCount')} "
        f"range: {summary.get('priceRangeMin')}–{summary.get('priceRangeMax')} "
        f"{summary.get('currency')}"
    )

    public = get_public_json(
        PUBLIC_TMPL.format(release_id=rid),
        user_agent=auth.get("USER_AGENT", DEFAULT_UA),
    )
    community = public.get("community") or {}
    print("\n# community (public api.discogs.com)")
    print(f"  have: {community.get('have')}  want: {community.get('want')}")
    print(
        f"  lowest_price: {public.get('lowest_price')} "
        f"num_for_sale: {public.get('num_for_sale')}"
    )

    gql = fetch_user_release(auth, rid)
    release = (gql.get("data") or {}).get("release") or {}
    viewer = (gql.get("data") or {}).get("viewer")
    if viewer is None and release.get("collectionItems") is None:
        print("\n# in-collection: viewer=null — session may be stale")
    else:
        coll = release.get("collectionItems") or {}
        edges = coll.get("edges") or []
        print(f"\n# in-collection (UserReleaseData) copies={coll.get('totalCount', len(edges))}")
        note_types = {}
        if viewer:
            for e in ((viewer.get("collectionNoteTypes") or {}).get("edges") or []):
                node = e.get("node") or {}
                note_types[node.get("discogsId")] = node.get("name")
        for e in edges:
            node = e.get("node") or {}
            folder = (node.get("folder") or {}).get("name")
            added = node.get("addedAt")
            notes = []
            for n in node.get("notes") or []:
                nt = (n.get("noteType") or {}).get("discogsId")
                label = note_types.get(nt) or f"noteType:{nt}"
                text = ((n.get("text") or {}).get("markup") or "").strip()
                if text:
                    notes.append(f"{label}={text}")
            print(f"  folder={folder!r} added={added} id={node.get('discogsId')}")
            if notes:
                print(f"    {'; '.join(notes)}")
        if not edges:
            print("  (not in collection)")
        want = release.get("inWantlist")
        print(f"  inWantlist={want}")


if __name__ == "__main__":
    cli_main(main)
