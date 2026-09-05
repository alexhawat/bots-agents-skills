#!/usr/bin/env python3
"""List releases in a Discogs series that are missing from the signed-in collection.

Uses public API for series members + ViewerCollectionListData (via _lib/collection_fetch)
for owned ids. No invented GraphQL. Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.collection_fetch import iter_collection_items  # noqa: E402
from _lib.discogs_search import PUBLIC_UA  # noqa: E402
from _lib.errors import DiscogsError, cli_main  # noqa: E402
from _lib.http import get_public_json  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
PUBLIC_RELEASE = "https://api.discogs.com/releases/{id}"
PUBLIC_SEARCH = "https://api.discogs.com/database/search"
DEFAULT_UA = "DiscogsScripts/1.0"


def ua(contact: str | None) -> str:
    base = DEFAULT_UA
    if contact:
        return f"{base} (+{contact})"
    # Prefer shared constant when present
    return PUBLIC_UA if PUBLIC_UA else base


def get_release(release_id: int, user_agent: str) -> dict:
    return get_public_json(PUBLIC_RELEASE.format(id=release_id), user_agent=user_agent)


def series_from_release(rel: dict) -> list[dict]:
    return list(rel.get("series") or [])


def pick_series(entries: list[dict], name: str | None) -> dict:
    if not entries:
        raise DiscogsError("release has no series[] — pass --series NAME instead")
    if name:
        needle = name.lower()
        for s in entries:
            if (s.get("name") or "").lower() == needle:
                return s
        for s in entries:
            if needle in (s.get("name") or "").lower():
                return s
        names = [s.get("name") for s in entries]
        raise DiscogsError(f"series {name!r} not on release; available={names}")
    if len(entries) == 1:
        return entries[0]
    names = [s.get("name") for s in entries]
    print(f"# multiple series on release; using first: {names[0]!r} (all={names})", file=sys.stderr)
    return entries[0]


def fetch_label_releases(resource_url: str, user_agent: str, limit: int | None) -> list[dict]:
    """Paginate label/series releases from resource_url (+ /releases)."""
    base = resource_url.rstrip("/")
    if not base.endswith("/releases"):
        # Discogs series usually point at /labels/{id}
        url = base + "/releases"
    else:
        url = base

    out: list[dict] = []
    page = 1
    per_page = 100
    while True:
        qs = urllib.parse.urlencode({"page": page, "per_page": per_page})
        data = get_public_json(f"{url}?{qs}", user_agent=user_agent)
        # label releases: {"releases":[...], "pagination":{...}}
        batch = data.get("releases") or data.get("results") or []
        for row in batch:
            # label /releases entries often have type=release|master
            rtype = (row.get("type") or "release").lower()
            if rtype not in ("release", ""):
                continue
            rid = row.get("id")
            if rid is None:
                continue
            out.append(
                {
                    "id": int(rid),
                    "title": row.get("title") or "",
                    "year": row.get("year") or "",
                    "catno": row.get("catno") or row.get("catalog_number") or "",
                    "artist": row.get("artist") or "",
                }
            )
            if limit is not None and len(out) >= limit:
                return out
        pag = data.get("pagination") or {}
        pages = int(pag.get("pages") or 1)
        if page >= pages or not batch:
            break
        page += 1
        if page > 200:
            break
        time.sleep(0.25)  # be polite to public API
    return out


def search_series_releases(series_name: str, user_agent: str, limit: int | None) -> list[dict]:
    """Fallback: database/search type=release q=series name; soft-filter by title."""
    out: list[dict] = []
    page = 1
    per_page = 100
    needle = series_name.lower()
    while True:
        qs = urllib.parse.urlencode(
            {
                "type": "release",
                "q": series_name,
                "page": page,
                "per_page": per_page,
            }
        )
        data = get_public_json(f"{PUBLIC_SEARCH}?{qs}", user_agent=user_agent)
        batch = data.get("results") or []
        for row in batch:
            title = row.get("title") or ""
            # Prefer hits that mention the series name somewhere
            blob = f"{title} {row.get('label') or ''} {row.get('catno') or ''}".lower()
            if needle not in blob and series_name.split()[0].lower() not in blob:
                continue
            rid = row.get("id")
            if rid is None:
                continue
            year = ""
            if row.get("year"):
                year = row["year"]
            catno = ""
            labels = row.get("label") or []
            if isinstance(labels, list) and labels:
                # sometimes catno is separate
                pass
            catno = (row.get("catno") or "") if isinstance(row.get("catno"), str) else ""
            out.append(
                {
                    "id": int(rid),
                    "title": title,
                    "year": year,
                    "catno": catno,
                    "artist": "",
                }
            )
            if limit is not None and len(out) >= limit:
                return _dedupe(out)
        pag = data.get("pagination") or {}
        pages = int(pag.get("pages") or 1)
        if page >= pages or not batch:
            break
        page += 1
        if page > 50:
            break
        time.sleep(0.25)
    return _dedupe(out)


def _dedupe(rows: list[dict]) -> list[dict]:
    seen: set[int] = set()
    out: list[dict] = []
    for r in rows:
        rid = int(r["id"])
        if rid in seen:
            continue
        seen.add(rid)
        out.append(r)
    return out


def resolve_series_members(
    *,
    series_meta: dict | None,
    series_name: str,
    user_agent: str,
    limit: int | None,
) -> list[dict]:
    if series_meta and series_meta.get("resource_url"):
        try:
            members = fetch_label_releases(
                series_meta["resource_url"], user_agent, limit
            )
            if members:
                return members
            print("# resource_url returned 0 releases; falling back to search", file=sys.stderr)
        except DiscogsError as e:
            print(f"# resource_url fetch failed: {e}; falling back to search", file=sys.stderr)

    return search_series_releases(series_name, user_agent, limit)


def owned_release_ids(auth: dict[str, str]) -> set[int]:
    ids: set[int] = set()
    for it in iter_collection_items(auth, progress=True):
        rel = it.get("release") or {}
        rid = rel.get("discogsId")
        if rid is not None:
            ids.add(int(rid))
    return ids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--series", metavar="NAME", help="Series name to resolve")
    g.add_argument(
        "--release-id",
        type=int,
        help="Derive series from public GET /releases/{id}",
    )
    ap.add_argument(
        "--limit-series",
        type=int,
        default=None,
        metavar="N",
        help="Cap number of series member releases fetched",
    )
    ap.add_argument("--json", action="store_true", help="Machine-readable JSON")
    ap.add_argument(
        "--contact",
        default=None,
        help="Optional contact for User-Agent (DiscogsScripts/1.0 +contact)",
    )
    ap.add_argument(
        "--skip-collection",
        action="store_true",
        help="Do not load owned ids (list series members only; owned empty)",
    )
    args = ap.parse_args()

    user_agent = ua(args.contact)
    series_meta: dict | None = None
    series_name: str

    if args.release_id is not None:
        rel = get_release(args.release_id, user_agent)
        entries = series_from_release(rel)
        series_meta = pick_series(entries, None)
        series_name = series_meta.get("name") or ""
        if not series_name:
            raise DiscogsError("series entry missing name")
    else:
        series_name = args.series
        # Try to find a series resource via a release search hit that lists series
        # Practical: search releases, take first with matching series resource_url
        qs = urllib.parse.urlencode(
            {"type": "release", "q": series_name, "per_page": 10, "page": 1}
        )
        try:
            hits = get_public_json(f"{PUBLIC_SEARCH}?{qs}", user_agent=user_agent)
            for hit in hits.get("results") or []:
                hid = hit.get("id")
                if not hid:
                    continue
                try:
                    full = get_release(int(hid), user_agent)
                except DiscogsError:
                    continue
                wanted = series_name.lower()
                for s in series_from_release(full):
                    got = (s.get("name") or "").lower()
                    if got == wanted or wanted in got:
                        series_meta = s
                        series_name = s.get("name") or series_name
                        break
                if series_meta:
                    break
                time.sleep(0.2)
        except DiscogsError as e:
            print(f"# series probe search skipped: {e}", file=sys.stderr)

    members = resolve_series_members(
        series_meta=series_meta,
        series_name=series_name,
        user_agent=user_agent,
        limit=args.limit_series,
    )

    owned: set[int] = set()
    if not args.skip_collection:
        auth = load_auth(task_root=TASK)
        owned = owned_release_ids(auth)

    missing = [m for m in members if m["id"] not in owned]
    owned_in_series = [m for m in members if m["id"] in owned]

    payload: dict[str, Any] = {
        "series": series_name,
        "series_id": (series_meta or {}).get("id"),
        "resource_url": (series_meta or {}).get("resource_url"),
        "members_fetched": len(members),
        "owned_count": len(owned_in_series),
        "missing_count": len(missing),
        "missing": missing,
        "owned": [
            {"id": m["id"], "title": m["title"], "year": m["year"], "catno": m.get("catno") or ""}
            for m in owned_in_series
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"series: {series_name}")
    if payload.get("series_id"):
        print(f"series_id: {payload['series_id']}")
    print(f"members fetched: {len(members)}")
    print(f"owned in series: {len(owned_in_series)}")
    print(f"missing: {len(missing)}")
    print("\nmissing releases:")
    if not missing:
        print("  (none)")
    for m in missing:
        year = m.get("year") or "?"
        catno = m.get("catno") or ""
        cat = f" catno={catno}" if catno else ""
        print(f"  {m['id']}: {m['title']} ({year}){cat}")
    print("\nowned (short):")
    if not owned_in_series:
        print("  (none)")
    for m in owned_in_series[:50]:
        year = m.get("year") or "?"
        print(f"  {m['id']}: {m['title']} ({year})")
    if len(owned_in_series) > 50:
        print(f"  … +{len(owned_in_series) - 50} more")
    return 0


if __name__ == "__main__":
    cli_main(main)
