#!/usr/bin/env python3
"""Replay Discogs ViewerCollectionListData (captured 2026-09-05).

Loads session auth from /home/box/discogs-auth/auth.env (preferred) or ../auth.env. Never prints secrets.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_AUTH = Path("/home/box/discogs-auth/auth.env")
AUTH_ENV = SHARED_AUTH if SHARED_AUTH.is_file() else (ROOT / "auth.env")

ENDPOINT = "https://www.discogs.com/service/catalog/api/graphql"
OPERATION = "ViewerCollectionListData"
# From capture/collection-federico.har (persisted query)
SHA256 = "ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b"
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def load_auth(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise SystemExit(
            f"Missing {path}. Re-capture: signed-in Cookie header → auth.env"
        )
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    if not out.get("COOKIE"):
        raise SystemExit(f"COOKIE= missing in {path}")
    return out


def graphql_get(auth: dict[str, str], variables: dict) -> dict:
    params = {
        "operationName": OPERATION,
        "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps(
            {"persistedQuery": {"version": 1, "sha256Hash": SHA256}},
            separators=(",", ":"),
        ),
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "apollographql-client-name": auth.get(
            "APOLLO_CLIENT_NAME", "release-page-client"
        ),
        "user-agent": auth.get("USER_AGENT", DEFAULT_UA),
        "referer": "https://www.discogs.com/",
        "cookie": auth["COOKIE"],
    }
    if auth.get("AUTHORIZATION"):
        headers["authorization"] = auth["AUTHORIZATION"]
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read()[:500]
        raise SystemExit(f"HTTP {e.code}: {body!r}") from e


def artist_blob(release: dict) -> str:
    parts = []
    for pa in release.get("primaryArtists") or []:
        name = pa.get("displayName") or (pa.get("artist") or {}).get("name") or ""
        if name:
            parts.append(name)
    return " / ".join(parts)


def format_blob(release: dict) -> str:
    bits = []
    for fmt in release.get("formats") or []:
        name = fmt.get("name") or ""
        qty = fmt.get("quantity") or "1"
        desc = ", ".join(fmt.get("description") or [])
        bits.append(f"{qty} x {name}" if qty not in ("1", 1, None) else name)
        if desc:
            bits.append(desc)
    return " — ".join(bits) if bits else ""


def is_vinyl(release: dict) -> bool:
    for fmt in release.get("formats") or []:
        if (fmt.get("name") or "").lower() == "vinyl":
            return True
    return False


def fetch_all(
    auth: dict[str, str],
    search: str,
    *,
    per_page: int = 50,
    folder_id: int = 0,
    currency: str = "EUR",
) -> list[dict]:
    page = 1
    items: list[dict] = []
    total = None
    while True:
        variables = {
            "page": page,
            "perPage": per_page,
            "currency": currency,
            "folderId": folder_id,
            "direction": "DESC",
            "field": "ADDED",
            "search": search,
        }
        data = graphql_get(auth, variables)
        viewer = (data.get("data") or {}).get("viewer")
        if viewer is None:
            raise SystemExit(
                "viewer=null — session dead or COOKIE incomplete. Re-login + re-export auth.env"
            )
        off = viewer.get("offsetCollectionItems") or {}
        batch = off.get("collectionItems") or []
        if total is None:
            total = off.get("totalCount")
            print(f"# totalCount={total} search={search!r}", file=sys.stderr)
        items.extend(batch)
        if not batch or (total is not None and len(items) >= total):
            break
        page += 1
        if page > 100:
            raise SystemExit("pagination safety stop")
    return items



def load_from_har(har_path: Path) -> list[dict]:
    har = json.loads(har_path.read_text())
    items: list[dict] = []
    for e in har["log"]["entries"]:
        url = e["request"]["url"]
        if "ViewerCollectionListData" not in url:
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
        raise SystemExit(f"No ViewerCollectionListData payloads in {har_path}")
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
    ap.add_argument("--auth", type=Path, default=AUTH_ENV)
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
        auth = load_auth(args.auth)
        items = fetch_all(auth, args.search, per_page=args.per_page)

    rows = []
    for it in items:
        rel = it.get("release") or {}
        if args.vinyl_only and not is_vinyl(rel):
            continue
        if args.artist_match:
            blob = artist_blob(rel).lower()
            if args.artist_match.lower() not in blob:
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
    else:
        # Dedupe display by release_id with counts
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
            year = r["year"] or "?"
            print(f"{i}. {r['title']} — {r['artists']} — {year} — {r['format']}{copies}")
            print(f"   {r['url']}")


if __name__ == "__main__":
    main()
