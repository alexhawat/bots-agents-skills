#!/usr/bin/env python3
"""Pre-push guard: refuse to push commits by untrusted authors.

Reads the allowlist from .github/trusted-authors.txt (one email per line,
case-insensitive, `#` comments) or from BOTS_TRUSTED_AUTHORS (comma-separated,
overrides the file entirely when set).

Usage: check_push_authors.py [<ref-range> ...]
With no arguments, inspects commits on the current branch that are not on the
default branch (origin/main). Exits 1 listing offending commits.

Invoked by hooks/pre-push (install with `make install-hooks`). Stdlib only.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = ROOT / ".github" / "trusted-authors.txt"


def trusted_emails() -> set[str]:
    override = os.environ.get("BOTS_TRUSTED_AUTHORS")
    if override:
        return {e.strip().lower() for e in override.split(",") if e.strip()}
    emails: set[str] = set()
    for line in ALLOWLIST.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            emails.add(line.lower())
    return emails


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def candidate_ranges() -> list[str]:
    if len(sys.argv) > 1:
        return sys.argv[1:]
    try:
        base = git("merge-base", "HEAD", "origin/main").strip()
    except subprocess.CalledProcessError:
        return ["HEAD"]  # no origin/main yet — check everything
    return [f"{base}..HEAD"]


def main() -> int:
    trusted = trusted_emails()
    if not trusted:
        print("trusted-authors: allowlist is empty — refusing to push", file=sys.stderr)
        return 1
    bad: list[str] = []
    for ref_range in candidate_ranges():
        out = git(
            "log", "--format=%H%x00%ae%x00%ce%x00%s", ref_range
        )
        for line in out.splitlines():
            if not line:
                continue
            sha, author, committer, subject = (line.split("\x00") + [""] * 4)[:4]
            if author.lower() not in trusted or committer.lower() not in trusted:
                bad.append(f"{sha[:10]} {subject} (author={author}, committer={committer})")
    if bad:
        print("trusted-authors: refusing to push — untrusted commit(s):", file=sys.stderr)
        for entry in bad:
            print(f"  {entry}", file=sys.stderr)
        print(
            "Add the email to .github/trusted-authors.txt or set "
            "BOTS_TRUSTED_AUTHORS to override.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
