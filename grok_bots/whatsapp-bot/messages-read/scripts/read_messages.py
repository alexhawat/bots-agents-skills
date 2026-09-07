#!/usr/bin/env python3
"""Read last N messages from a chat — opaque HTTP until capture; headless CDP supported."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from _lib.opaque import require_http_or_exit  # noqa: E402


def browser_procedure(chat: str, limit: int) -> None:
    print(f"# mode=browser — browserUse procedure for chat={chat!r} limit={limit}")
    print("# 1. Open https://web.whatsapp.com/ (linked session)")
    print(f"# 2. Find and open chat matching name/jid: {chat}")
    print(f"# 3. Scroll message pane to load ~{limit} recent messages")
    print("# 4. For each message record: direction (in/out), timestamp text, body preview, message-id if in DOM")
    print("# 5. Do not invent HTTP/WS replay; no media download here (see media-download)")


def headless(chat: str, limit: int) -> int:
    from _lib.headless_runner import run_headless  # noqa: E402

    data = run_headless("read-messages", {"chat": chat, "limit": limit})
    print(json.dumps(data, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chat", required=True, help="Chat display name or jid")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--mode", choices=("browser", "http", "headless"), default="browser")
    args = ap.parse_args()

    if args.mode == "browser":
        browser_procedure(args.chat, args.limit)
        return 0
    if args.mode == "headless":
        return headless(args.chat, args.limit)

    require_http_or_exit(TASK, "messages-read")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
