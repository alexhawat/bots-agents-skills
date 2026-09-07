#!/usr/bin/env python3
"""Search chats/contacts — opaque HTTP until capture; headless CDP supported."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from _lib.errors import cli_main  # noqa: E402
from _lib.opaque import require_http_or_exit  # noqa: E402


def browser_procedure(query: str) -> None:
    print(f"# mode=browser — browserUse procedure for query={query!r}")
    print("# 1. Open https://web.whatsapp.com/ (linked session)")
    print("# 2. Focus the chat search / filter box in the left pane")
    print(f"# 3. Type query: {query}")
    print("# 4. Record matching chat/contact rows (name + subtitle); no invented API")


def headless(query: str, limit: int) -> int:
    from _lib.headless_runner import run_headless  # noqa: E402

    data = run_headless("search-chats", {"query": query, "limit": limit})
    print(json.dumps(data, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--mode", choices=("browser", "http", "headless"), default="browser")
    args = ap.parse_args()

    if args.mode == "browser":
        browser_procedure(args.query)
        return 0
    if args.mode == "headless":
        return headless(args.query, args.limit)

    require_http_or_exit(TASK, "chats-search")
    return 2


if __name__ == "__main__":
    cli_main(main)
