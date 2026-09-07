#!/usr/bin/env python3
"""Contact profile/about — opaque HTTP until capture."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from _lib.cli import die  # noqa: E402
from _lib.opaque import require_http_or_exit  # noqa: E402


def browser_procedure(target: str) -> None:
    print(f"# mode=browser — browserUse procedure for contact={target!r}")
    print("# 1. Open https://web.whatsapp.com/")
    print(f"# 2. Open chat / contact info panel for: {target}")
    print("# 3. Record display name, about/status text, groups-in-common count if shown")
    print("# 4. Do not scrape or log phone numbers into public files unless required and scrubbed")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chat", default=None)
    ap.add_argument("--jid", default=None)
    ap.add_argument("--mode", choices=("browser", "http"), default="browser")
    args = ap.parse_args()

    if not args.chat and not args.jid:
        die("provide --chat or --jid", 1)
    target = args.chat or args.jid

    if args.mode == "browser":
        browser_procedure(target)
        return 0

    require_http_or_exit(TASK, "contact-info")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
