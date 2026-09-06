#!/usr/bin/env python3
"""Fail if a committed HAR still carries live session material.

A raw capture holds the Cookie that authenticates the whole account, so HARs
are denied by default in .gitignore and only hand-redacted fixtures are
allowlisted. This guard is the backstop for that discipline.

HAR stores credentials in more than one place, and a capture tool may populate
any subset of them:

  * ``request.headers[]``   — ``Cookie`` / ``Authorization``
  * ``request.cookies[]``   — the parsed form of the same header
  * ``response.headers[]``  — ``Set-Cookie``
  * ``response.cookies[]``  — its parsed form

Checking only request headers (as the first version of this guard did) passes a
file whose ``cookies[]`` array is full of live values. All four are checked.

Usage:  har_guard.py FILE [FILE ...]
Exit 0 when every file is clean, 1 on the first file with a finding.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# Values a redacted fixture is allowed to carry in a credential slot.
PLACEHOLDERS = {"", "redacted", "placeholder", "<redacted>", "<placeholder>", "-", "n/a"}

CREDENTIAL_HEADERS = {"cookie", "authorization", "set-cookie", "x-api-key"}


def _is_redacted(value: Any) -> bool:
    return str(value or "").strip().lower() in PLACEHOLDERS


def _headers(container: dict, where: str) -> Iterator[str]:
    for header in container.get("headers") or []:
        name = str(header.get("name") or "").lower()
        if name in CREDENTIAL_HEADERS and not _is_redacted(header.get("value")):
            yield f"{where}.headers[{name}]"


def _cookies(container: dict, where: str) -> Iterator[str]:
    """The parsed cookie array — populated by some tools even when headers are stripped."""
    for cookie in container.get("cookies") or []:
        if not _is_redacted(cookie.get("value")):
            yield f"{where}.cookies[{cookie.get('name') or '?'}]"


def scan_har(path: Path) -> list[str]:
    """Return a list of leak locations. Empty means the file is clean."""
    try:
        har = json.loads(path.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError) as e:
        # An unparseable .har cannot be shown to be redacted, so treat it as suspect.
        return [f"unreadable ({e.__class__.__name__}) — cannot verify redaction"]

    findings: list[str] = []
    entries = ((har.get("log") or {}).get("entries")) or []
    for i, entry in enumerate(entries):
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        for loc in _headers(request, "request"):
            findings.append(f"entry[{i}].{loc}")
        for loc in _cookies(request, "request"):
            findings.append(f"entry[{i}].{loc}")
        for loc in _headers(response, "response"):
            findings.append(f"entry[{i}].{loc}")
        for loc in _cookies(response, "response"):
            findings.append(f"entry[{i}].{loc}")
    return findings


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]]
    if not paths:
        print("usage: har_guard.py FILE [FILE ...]", file=sys.stderr)
        return 2

    failed = False
    for path in paths:
        findings = scan_har(path)
        if findings:
            failed = True
            # GitHub Actions annotation; harmless plain text elsewhere.
            print(f"::error file={path}::unredacted session material in committed HAR")
            for f in findings:
                print(f"    {f}")
        else:
            print(f"ok: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
