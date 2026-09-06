#!/usr/bin/env python3
"""Check Discogs session (viewer) and optionally re-export Cookie from Chrome.

Uses ViewerCollectionListData (same sha as whoami) with minimal vars.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.errors import (  # noqa: E402
    DiscogsAuthError,
    DiscogsError,
    DiscogsHTTPError,
    cli_main,
)
from _lib.http import graphql_get  # noqa: E402

TASK = Path(__file__).resolve().parents[1]
GRAPHQL = "https://www.discogs.com/service/catalog/api/graphql"
LIST_SHA = "ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b"
EXPORT_COOKIES = Path("/home/box/discogs-auth/export_cookies.py")

SEMI_MANUAL = """\
session dead after refresh attempt.
Semi-manual path:
  1) Sign in to Discogs in Discogs-Bot's own Chrome on this box
     (request_box_help for login/2FA/captcha — agent never sees secrets).
  2) Re-run: python3 auth-refresh/scripts/refresh.py
     — prefers auto-import: export_cookies.py → Cookie saved to auth.env
     — or: python3 /home/box/discogs-auth/export_cookies.py
     — or paste Cookie header into /home/box/discogs-auth/auth.env as COOKIE=...
     (never paste Cookie into chat).
"""


def check_viewer(auth: dict[str, str]) -> tuple[str | None, str | None]:
    """Return (status, identity). status is 'ok', 'null', or 'http401'."""
    variables = {
        "page": 1,
        "perPage": 1,
        "currency": "EUR",
        "folderId": 0,
        "direction": "DESC",
        "field": "ADDED",
        "search": "",
    }
    try:
        data = graphql_get(
            auth,
            endpoint=GRAPHQL,
            operation_name="ViewerCollectionListData",
            sha256_hash=LIST_SHA,
            variables=variables,
        )
    except DiscogsHTTPError as e:
        # 401/403 both mean "this jar is no longer accepted" for refresh purposes.
        if e.status in (401, 403):
            return "http401", None
        raise
    except DiscogsAuthError:
        # viewer=null surfaced from the shared fetch helper.
        return "null", None

    viewer = (data.get("data") or {}).get("viewer")
    if viewer is None:
        return "null", None

    username = viewer.get("username")
    discogs_id = viewer.get("discogsId")
    identity = username or (str(discogs_id) if discogs_id is not None else "unknown")
    return "ok", identity


def run_export() -> int:
    if not EXPORT_COOKIES.is_file():
        print(f"export helper missing: {EXPORT_COOKIES}", file=sys.stderr)
        return 1
    print(f"# running {EXPORT_COOKIES}", file=sys.stderr)
    proc = subprocess.run(
        [sys.executable, str(EXPORT_COOKIES)],
        capture_output=True,
        text=True,
    )
    # Forward stdout/stderr from export (already redacted — no cookie values)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check-only",
        action="store_true",
        help="Only check viewer; never run export_cookies.py",
    )
    ap.add_argument(
        "--force-export",
        action="store_true",
        help="Always try export_cookies.py first, then check",
    )
    args = ap.parse_args()

    if args.check_only and args.force_export:
        ap.error("use either --check-only or --force-export, not both")

    if args.force_export:
        rc = run_export()
        if rc != 0:
            print("# export_cookies failed; will still re-check existing auth.env", file=sys.stderr)

    auth = load_auth(task_root=TASK)
    status, identity = check_viewer(auth)

    if status == "ok":
        # Prefer USERNAME from auth.env when GraphQL viewer has only discogsId
        if identity.isdigit() and auth.get("USERNAME"):
            identity = auth["USERNAME"]
        print(f"ok viewer={identity}")
        return 0

    if args.check_only:
        print(f"dead viewer status={status} (--check-only; no export)")
        print(SEMI_MANUAL, end="")
        return 1

    if not args.force_export:
        print(f"# viewer status={status}; trying export_cookies.py", file=sys.stderr)
        run_export()
        auth = load_auth(task_root=TASK)
        status, identity = check_viewer(auth)
        if status == "ok":
            if identity.isdigit() and auth.get("USERNAME"):
                identity = auth["USERNAME"]
            print(f"ok viewer={identity}")
            return 0

    # force-export path already exported once; re-check after that export
    if args.force_export:
        auth = load_auth(task_root=TASK)
        status, identity = check_viewer(auth)
        if status == "ok":
            if identity.isdigit() and auth.get("USERNAME"):
                identity = auth["USERNAME"]
            print(f"ok viewer={identity}")
            return 0

    print(f"dead viewer status={status}")
    print(SEMI_MANUAL, end="")
    return 1


def _main() -> int:
    """Wrap main so a transport failure reads as an error, not a traceback."""
    try:
        return main()
    except urllib.error.URLError as e:
        raise DiscogsError(f"network error: {e}") from e


if __name__ == "__main__":
    cli_main(_main)
