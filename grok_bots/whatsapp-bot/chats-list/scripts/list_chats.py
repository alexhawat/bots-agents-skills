#!/usr/bin/env python3
"""List recent WhatsApp chats — HTTP opaque until capture; browser/headless modes."""
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


def browser_procedure() -> None:
    print("# mode=browser — browserUse procedure (no HTTP replay)")
    print("# 1. Open https://web.whatsapp.com/ (linked session; chat list visible)")
    print("# 2. Scroll the left chat sidebar to cover recent conversations")
    print("# 3. For each visible row, record: display name, unread badge, last message preview")
    print("# 4. Prefer DOM/accessibility tree; do not invent API calls")
    print("# 5. Output lines: name | unread | preview  (no secrets)")


def headless(limit: int) -> int:
    from _lib.headless_runner import run_headless  # noqa: E402

    data = run_headless("list-chats", {"limit": limit})
    print(json.dumps(data, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--mode",
        choices=("browser", "http", "headless"),
        default="browser",
        help="browser=UI docs; headless=CDP DOM; http=replay only if capture exists",
    )
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    if args.mode == "browser":
        browser_procedure()
        return 0
    if args.mode == "headless":
        return headless(args.limit)

    eps = require_http_or_exit(TASK, "chats-list")
    print(f"# http mode: {len(eps)} captured endpoint(s) — implement replay after capture review")
    for e in eps:
        print(f"# endpoint method={e.get('method','?')} url_host_path_only=redacted_until_reviewed")
    print("# refusing blind replay of unreviewed capture shapes", file=sys.stderr)
    return 2


if __name__ == "__main__":
    cli_main(main)
