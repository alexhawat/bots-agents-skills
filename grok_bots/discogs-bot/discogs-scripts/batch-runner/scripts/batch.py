#!/usr/bin/env python3
"""One CLI wrapping existing Discogs search scripts via subprocess.

Examples:
  batch.py search collection --q TEXT [--vinyl-only]
  batch.py search wantlist --q TEXT
  batch.py search market --q TEXT [--format Vinyl] [--currency EUR]

Prints the invoked script path (no secrets). Passes through exit codes.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[2]

TARGETS = {
    "collection": SCRIPTS_ROOT / "collection-search" / "scripts" / "search_collection.py",
    "wantlist": SCRIPTS_ROOT / "mywantlist-search" / "scripts" / "search.py",
    "market": SCRIPTS_ROOT / "marketplace-search" / "scripts" / "search.py",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    search = sub.add_parser("search", help="Delegate to collection / wantlist / market search")
    search.add_argument(
        "target",
        choices=("collection", "wantlist", "market"),
        help="Which search script to run",
    )
    search.add_argument("--q", required=True, help="Search query text")
    search.add_argument(
        "--vinyl-only",
        action="store_true",
        help="collection only: pass --vinyl-only",
    )
    search.add_argument(
        "--format",
        default="Vinyl",
        dest="format_name",
        help="market only: format filter (default Vinyl)",
    )
    search.add_argument(
        "--currency",
        default="EUR",
        help="market only: currency (default EUR)",
    )

    args = ap.parse_args()

    if args.cmd != "search":
        ap.error(f"unknown command {args.cmd}")

    script = TARGETS[args.target]
    if not script.is_file():
        print(f"missing script: {script}", file=sys.stderr)
        return 1

    cmd: list[str] = [sys.executable, str(script)]

    if args.target == "collection":
        cmd.append(args.q)
        if args.vinyl_only:
            cmd.append("--vinyl-only")
    elif args.target == "wantlist":
        cmd.append(args.q)
        if args.vinyl_only:
            print("# warning: --vinyl-only ignored for wantlist", file=sys.stderr)
    elif args.target == "market":
        cmd.append(args.q)
        cmd.extend(["--format", args.format_name, "--currency", args.currency])
        if args.vinyl_only:
            print("# warning: --vinyl-only ignored for market (use --format)", file=sys.stderr)

    print(f"# invoked {script}")
    proc = subprocess.run(cmd)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
