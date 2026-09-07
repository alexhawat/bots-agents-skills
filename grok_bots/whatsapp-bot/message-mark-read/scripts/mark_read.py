#!/usr/bin/env python3
"""Mark a WhatsApp chat read — requires --confirm; HTTP opaque until capture."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from _lib.opaque import require_http_or_exit  # noqa: E402


def dry_run(chat: str) -> None:
    print("# dry-run: would mark chat read (no action taken)")
    print(f"# chat={chat!r}")
    print("# pass --confirm to proceed")


def browser_mark(chat: str) -> None:
    print(f"# mode=browser --confirm — browserUse steps")
    print("# 1. Open https://web.whatsapp.com/ (linked session)")
    print(f"# 2. Open chat matching: {chat}")
    print("# 3. Ensure message pane is focused/visible so WA marks read (blue ticks / unread clear)")
    print("# 4. Do not invent receipt API calls")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chat", required=True)
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--mode", choices=("browser", "http"), default="browser")
    args = ap.parse_args()

    if not args.confirm:
        dry_run(args.chat)
        return 0

    if args.mode == "browser":
        browser_mark(args.chat)
        return 0

    require_http_or_exit(TASK, "message-mark-read")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
