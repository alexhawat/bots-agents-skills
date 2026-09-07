#!/usr/bin/env python3
"""auth-check: verify COOKIE + USER_AGENT keys exist (never print values)."""
from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load  # noqa: E402
from _lib.cli import ok  # noqa: E402

REQUIRED = ("COOKIE", "USER_AGENT")
EXPORT = Path("/home/box/whatsapp-auth/export_cookies.py")
PROBE_URL = "https://web.whatsapp.com/"


def check_keys(env: dict[str, str]) -> tuple[list[str], list[str]]:
    present = [k for k in REQUIRED if env.get(k)]
    missing = [k for k in REQUIRED if not env.get(k)]
    return present, missing


def weak_probe(env: dict[str, str]) -> None:
    cookie = env.get("COOKIE") or ""
    ua = env.get("USER_AGENT") or "WhatsApp-Bot-auth-check"
    if not cookie:
        print("# probe skipped (no COOKIE)")
        return
    req = urllib.request.Request(
        PROBE_URL,
        headers={
            "User-Agent": ua,
            "Cookie": cookie,
            "Accept": "text/html,application/xhtml+xml",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"# probe GET {PROBE_URL} status={resp.status}")
    except urllib.error.HTTPError as e:
        print(f"# probe GET {PROBE_URL} status={e.code}")
    except Exception as e:
        print(f"# probe error type={type(e).__name__}")
    print("# note: 200 ≠ fully authed for WhatsApp Web; chat-list in Chrome is proof")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--export",
        action="store_true",
        help="Run export_cookies.py then re-check keys",
    )
    ap.add_argument(
        "--no-probe",
        action="store_true",
        help="Skip weak HTTP GET probe",
    )
    args = ap.parse_args()

    if args.export:
        if not EXPORT.is_file():
            print(f"dead missing=export_helper path={EXPORT}", file=sys.stderr)
            return 1
        print(f"# running {EXPORT}")
        r = subprocess.run([sys.executable, str(EXPORT)])
        if r.returncode != 0:
            print(f"# export exit={r.returncode}", file=sys.stderr)

    env = load()
    present, missing = check_keys(env)
    if missing:
        print(f"dead missing={missing}")
        return 1

    ok(f"ok keys={present}")
    if not args.no_probe:
        weak_probe(env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
