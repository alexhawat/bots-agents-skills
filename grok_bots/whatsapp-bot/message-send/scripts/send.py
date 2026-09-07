#!/usr/bin/env python3
"""Send a WhatsApp text message — requires --confirm; HTTP opaque; headless CDP supported."""
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


def dry_run(chat: str, text: str) -> None:
    print("# dry-run: would send message (no action taken)")
    print(f"# chat={chat!r}")
    print(f"# text_len={len(text)}")
    print("# pass --confirm to proceed (browser docs, headless CDP, or http after capture)")


def browser_send(chat: str, text: str) -> None:
    print("# mode=browser --confirm — browserUse steps for ONE message")
    print("# 1. Open https://web.whatsapp.com/ (linked session)")
    print(f"# 2. Open chat matching: {chat}")
    print("# 3. Focus the message compose box")
    print(f"# 4. Type text (len={len(text)}); do not paste secrets from auth.env")
    print("# 5. Click Send / press Enter once")
    print("# 6. Confirm the outgoing bubble appears; stop (no loops, no mass send)")


def headless_send(chat: str, text: str, confirm: bool) -> int:
    from _lib.headless_runner import run_headless  # noqa: E402

    extra = ["--confirm"] if confirm else []
    data = run_headless("send-text", {"chat": chat, "text": text, "confirm": confirm}, extra=extra)
    print(json.dumps(data, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chat", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--confirm", action="store_true", help="Required to leave dry-run / real send")
    ap.add_argument("--mode", choices=("browser", "http", "headless"), default="browser")
    args = ap.parse_args()

    if args.mode == "headless":
        if not args.confirm:
            dry_run(args.chat, args.text)
            return 0
        return headless_send(args.chat, args.text, True)

    if not args.confirm:
        dry_run(args.chat, args.text)
        return 0

    if args.mode == "browser":
        browser_send(args.chat, args.text)
        return 0

    require_http_or_exit(TASK, "message-send")
    return 2


if __name__ == "__main__":
    cli_main(main)
