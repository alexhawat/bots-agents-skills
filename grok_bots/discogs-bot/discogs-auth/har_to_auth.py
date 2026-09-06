#!/usr/bin/env python3
"""Write COOKIE from a HAR request header into auth.env. Never prints Cookie values."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Resolved per call, not at import — see export_cookies.py.
def out_path() -> Path:
    """Match _lib.auth resolution so exporter and loader never disagree."""
    if os.environ.get("DISCOGS_AUTH_ENV"):
        return Path(os.environ["DISCOGS_AUTH_ENV"])
    base = os.environ.get("DISCOGS_AUTH_DIR") or "/home/box/discogs-auth"
    return Path(base) / "auth.env"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def best_cookie(har: dict) -> tuple[str, str] | None:
    best = None
    for e in har.get("log", {}).get("entries", []):
        req_headers = e.get("request", {}).get("headers", [])
        headers = {h.get("name", "").lower(): h.get("value") or "" for h in req_headers}
        cookie = headers.get("cookie") or ""
        if not cookie or "REDACTED" in cookie.upper():
            continue
        names = {p.split("=", 1)[0].strip() for p in cookie.split(";") if "=" in p}
        score = len(cookie)
        if "session" in names:
            score += 10_000
        if "sid" in names:
            score += 5_000
        if best is None or score > best[0]:
            ua = headers.get("user-agent") or UA
            best = (score, cookie, ua)
    if not best:
        return None
    return best[1], best[2]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: har_to_auth.py <file.har>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"fail: no such HAR: {path}")
        return 1
    try:
        har = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"fail: {path} is not valid JSON: {e}")
        return 1
    got = best_cookie(har)
    if not got:
        print(f"fail: no usable Cookie header in {path}")
        return 1
    cookie, ua = got
    names = sorted({p.split("=", 1)[0].strip() for p in cookie.split(";") if "=" in p})
    # Create at 0600 before writing: write_text() would create at the umask
    # default (0644), leaving the cookie world-readable until the chmod.
    out = out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, f"COOKIE={cookie}\nUSER_AGENT={ua}\n".encode())
    finally:
        os.close(fd)
    os.chmod(out, 0o600)
    print(f"ok path={out} cookie_len={len(cookie)} names={names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
