#!/usr/bin/env python3
"""Download WhatsApp media — opaque HTTP until capture; browser docs only for now."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from _lib.opaque import require_http_or_exit  # noqa: E402


def browser_procedure(message_id: str, out: Path) -> None:
    print(f"# mode=browser — browserUse procedure message_id={message_id!r} out={out}")
    print("# 1. Open the chat containing the message (use messages-read / UI search)")
    print("# 2. Locate the message bubble / media thumbnail for that id if exposed in DOM")
    print("# 3. Open media viewer / download control in the UI")
    print(f"# 4. Save file to {out} via browser download path (box downloads folder)")
    print("# 5. HTTP CDN URLs must come from capture — do not invent mmg.whatsapp.net paths")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--message-id", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("browser", "http"), default="browser")
    args = ap.parse_args()

    if args.mode == "browser":
        browser_procedure(args.message_id, args.out)
        return 0

    require_http_or_exit(TASK, "media-download")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
