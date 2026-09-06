#!/usr/bin/env python3
"""List Discogs artist discography (releases/masters) via public API.

Resolve artist with site autocomplete (_lib.discogs_search.autocomplete) or --artist-id.
Documented: GET https://api.discogs.com/artists/{id}/releases
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
from _lib.discogs_search import PUBLIC_UA, autocomplete  # noqa: E402
from _lib.errors import DiscogsError, cli_main  # noqa: E402
from _lib.http import get_public_json  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
RELEASES_TMPL = "https://api.discogs.com/artists/{artist_id}/releases"


def resolve_artist_id(name: str, auth: dict | None) -> tuple[int, str]:
    hits = autocomplete(
        name,
        auth,
        search_type="ARTIST",
    )
    artists = [
        h
        for h in hits
        if (h.kind or "").lower() in ("artist",) or h.kind == "Artist"
    ]
    if not artists:
        # Fallback: any hit that looks like artist from public-ish autocomplete
        artists = [h for h in hits if "artist" in (h.kind or "").lower()]
    if not artists:
        raise DiscogsError(f"No artist autocomplete hit for {name!r}")
    best = artists[0]
    return best.discogs_id, best.title or name


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "artist",
        nargs="?",
        help="Artist name (resolved via autocomplete unless --artist-id)",
    )
    ap.add_argument("--artist-id", type=int, help="Skip autocomplete; use this id")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--per-page", type=int, default=50)
    ap.add_argument(
        "--role",
        default=None,
        help="Filter by role (e.g. Main, Appearance, TrackAppearance)",
    )
    ap.add_argument(
        "--sort",
        default="year",
        choices=("year", "title", "format"),
        help="Public API sort field (default year)",
    )
    ap.add_argument(
        "--sort-order",
        default="desc",
        choices=("asc", "desc"),
    )
    args = ap.parse_args()

    if not args.artist_id and not args.artist:
        ap.error("Provide ARTIST name or --artist-id")

    auth = None
    try:
        auth = load_auth(task_root=TASK)
    except DiscogsError:
        auth = None

    if args.artist_id:
        artist_id = args.artist_id
        artist_label = args.artist or str(artist_id)
    else:
        artist_id, artist_label = resolve_artist_id(args.artist, auth)

    params = {
        "sort": args.sort,
        "sort_order": args.sort_order,
        "page": args.page,
        "per_page": args.per_page,
    }
    url = f"{RELEASES_TMPL.format(artist_id=artist_id)}?{urlencode(params)}"
    data = get_public_json(url, user_agent=PUBLIC_UA)
    releases = data.get("releases") or []
    pag = data.get("pagination") or {}

    role_filter = (args.role or "").strip().lower() or None
    if role_filter:
        releases = [r for r in releases if (r.get("role") or "").lower() == role_filter]

    print(
        f"# artist={artist_label!r} id={artist_id} "
        f"page={pag.get('page')}/{pag.get('pages')} "
        f"items={pag.get('items')} showing={len(releases)}"
        + (f" role={args.role!r}" if role_filter else "")
    )
    for r in releases:
        rid = r.get("id")
        typ = r.get("type") or ""
        title = r.get("title") or ""
        year = r.get("year") or ""
        fmt = r.get("format") or ""
        role = r.get("role") or ""
        print(f"{rid}\t{typ}\t{title}\t{year}\t{fmt}\t{role}")


if __name__ == "__main__":
    cli_main(main)
