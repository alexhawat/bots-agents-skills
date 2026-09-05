#!/usr/bin/env python3
"""Search Discogs /mywantlist (HTML list pages). Captured 2026-09-05."""
from __future__ import annotations

import argparse
import html as htmlmod
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from _lib.auth import load_auth  # noqa: E402
from _lib.errors import cli_main  # noqa: E402
from _lib.http import get_text  # noqa: E402

ROW_RE = re.compile(
    r'<tr[^>]*class="[^"]*wantlist_r(\d+)[^"]*"[^>]*>(.*?)</tr>', re.S | re.I
)


def parse_rows(page_html: str) -> list[dict]:
    rows: list[dict] = []
    for m in ROW_RE.finditer(page_html):
        rid, body = m.group(1), m.group(2)
        artists = [
            htmlmod.unescape(a.strip())
            for a in re.findall(r'href="/artist/\d+[^"]*"[^>]*>([^<]+)</a>', body)
        ]
        title_m = re.search(
            r'class="release_title_link"[^>]*>\s*<a[^>]+href="(/release/[^"]+)"[^>]*>([^<]+)</a>',
            body,
            re.S,
        )
        if not title_m:
            title_m = re.search(
                rf'href="(/release/{rid}[^"]*)"[^>]*>([^<]+)</a>', body
            )
        title = htmlmod.unescape(title_m.group(2).strip()) if title_m else ""
        href = title_m.group(1) if title_m else f"/release/{rid}"
        if href.startswith("/"):
            href = "https://www.discogs.com" + href.split("?")[0]
        # format / year if present
        fmt = ""
        fm = re.search(r'class="format"[^>]*>(.*?)</', body, re.S)
        if fm:
            fmt = htmlmod.unescape(re.sub("<[^>]+>", " ", fm.group(1)))
            fmt = re.sub(r"\s+", " ", fmt).strip()
        rows.append(
            {
                "release_id": int(rid),
                "title": title,
                "artists": " / ".join(artists),
                "url": href,
                "format": fmt,
            }
        )
    return rows


def fetch_all(auth: dict, search: str, max_pages: int = 50) -> list[dict]:
    all_rows: list[dict] = []
    page = 1
    while page <= max_pages:
        q = {"search": search, "page": str(page)} if search else {"page": str(page)}
        if not search:
            q.pop("search", None)
            url = "https://www.discogs.com/mywantlist"
            if page > 1:
                url += "?" + urllib.parse.urlencode({"page": page})
        else:
            url = "https://www.discogs.com/mywantlist?" + urllib.parse.urlencode(
                {"search": search, "page": page}
            )
        html = get_text(url, auth)
        rows = parse_rows(html)
        print(f"# page={page} rows={len(rows)}", file=sys.stderr)
        if not rows:
            break
        all_rows.extend(rows)
        # stop if no next page link
        if page > 1 and f"page={page + 1}" not in html and not re.search(
            rf'page={page + 1}(?:&|"|\')', html
        ):
            # also stop when fewer than a full page (~25)
            if len(rows) < 25:
                break
        elif f"page={page + 1}" not in html and page == 1 and len(rows) < 25:
            break
        if f"page={page + 1}" not in html:
            break
        page += 1
    # dedupe by release_id
    seen = set()
    out = []
    for r in all_rows:
        if r["release_id"] in seen:
            continue
        seen.add(r["release_id"])
        out.append(r)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("search", nargs="?", default="", help="Wantlist search string")
    ap.add_argument(
        "--artist-match",
        metavar="SUBSTR",
        help="Keep rows whose artist text contains SUBSTR (case-insensitive)",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    auth = load_auth(Path(__file__).resolve().parents[1])
    rows = fetch_all(auth, args.search.strip())
    if args.artist_match:
        needle = args.artist_match.lower()
        rows = [r for r in rows if needle in (r["artists"] or "").lower()]
    if args.json:
        import json

        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print(f"{len(rows)} wantlist releases\n")
        for i, r in enumerate(rows, 1):
            arts = r["artists"] or "?"
            print(f"{i}. {r['title']} — {arts}")
            print(f"   {r['url']}")


if __name__ == "__main__":
    cli_main(main)
