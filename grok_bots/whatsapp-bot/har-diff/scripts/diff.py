#!/usr/bin/env python3
"""Compare HAR or URL list to expected-urls.json. Never prints cookies."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

TASK = Path(__file__).resolve().parents[1]
DEFAULT_EXPECTED = TASK / "capture" / "expected-urls.json"

COOKIE_RE = re.compile(r"(?i)(cookie|authorization|token|wa_web_access)\s*[:=]")
URL_RE = re.compile(r"https?://[^\s\"']+")


def normalize(url: str) -> str:
    p = urlparse(url.strip())
    if not p.scheme:
        return url.strip()
    path = p.path or "/"
    return f"{p.scheme}://{p.netloc}{path}"


def load_expected(path: Path) -> list[str]:
    data = json.loads(path.read_text())
    urls = data.get("urls") if isinstance(data, dict) else data
    if not isinstance(urls, list):
        raise SystemExit(f"expected-urls: need urls list in {path}")
    return [normalize(u) for u in urls if isinstance(u, str) and u.strip()]


def _clean_url(raw: str) -> str:
    return normalize(raw.rstrip("),;]\"'"))


def extract_from_text(text: str) -> set[str]:
    found: set[str] = set()
    for line in text.splitlines():
        if COOKIE_RE.search(line):
            continue
        for m in URL_RE.findall(line):
            found.add(_clean_url(m))
    return found


def extract_from_har(path: Path) -> set[str]:
    raw = path.read_text(errors="replace")
    try:
        har = json.loads(raw)
    except json.JSONDecodeError:
        return extract_from_text(raw)
    found: set[str] = set()
    for entry in ((har.get("log") or {}).get("entries")) or []:
        req = entry.get("request") or {}
        url = req.get("url") or ""
        if url:
            found.add(normalize(url))
        # deliberately ignore headers (cookies live there)
    return found


def extract(path: Path) -> set[str]:
    if path.name.lower().endswith(".har"):
        return extract_from_har(path)
    return extract_from_text(path.read_text(errors="replace"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="HAR or URL list text file")
    ap.add_argument(
        "--expected",
        type=Path,
        default=DEFAULT_EXPECTED,
        help=f"expected-urls.json (default {DEFAULT_EXPECTED})",
    )
    args = ap.parse_args()

    if not args.path.is_file():
        print(f"not found: {args.path}", file=sys.stderr)
        return 1
    if not args.expected.is_file():
        print(f"expected fixture missing: {args.expected}", file=sys.stderr)
        return 1

    expected = load_expected(args.expected)
    observed = extract(args.path)

    matched = sorted(u for u in expected if u in observed)
    missing = sorted(u for u in expected if u not in observed)
    new_urls = sorted(u for u in observed if u not in set(expected))

    print(f"# har-diff input={args.path} expected={args.expected}")
    print(f"matched ({len(matched)}):")
    for u in matched:
        print(f"  ok {u}")
    print(f"new urls ({len(new_urls)}):")
    for u in new_urls:
        print(f"  + {u}")
    print(f"missing expected ({len(missing)}):")
    for u in missing:
        print(f"  - {u}")

    if expected and missing:
        print("# result: FAIL (missing expected urls)")
        return 1
    print("# result: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
