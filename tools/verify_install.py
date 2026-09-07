#!/usr/bin/env python3
"""Verify a bot install on any infra (grok box, Hermes, OpenClaw, local).

Checks the things every pack README tells you to set up, then optionally runs
the bots' own offline/auth probes. Read-only: it never writes auth material
and never prints secret values.

Usage:
    python3 tools/verify_install.py --bot discogs [--probe]
    python3 tools/verify_install.py --bot whatsapp [--probe]

Exit 0 when every check passes, 1 otherwise. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "ok" if ok else "FAIL"
    suffix = f" — {detail}" if detail and not ok else ""
    print(f"[{mark}] {label}{suffix}")
    return ok


def find_clone() -> Path | None:
    """The running repo if it contains grok_bots/, else $BOTS_REPO_ROOT."""
    if (ROOT / "grok_bots").is_dir():
        return ROOT
    candidate = Path(os.environ.get("BOTS_REPO_ROOT", "~/bots-agents-skills")).expanduser()
    return candidate if (candidate / "grok_bots").is_dir() else None


def verify_discogs(clone: Path, probe: bool) -> bool:
    ok = True
    pack = clone / "grok_bots" / "discogs-bot"
    ok &= check("discogs pack present", (pack / "discogs-scripts" / "_lib").is_dir())
    auth_dir = Path(os.environ.get("DISCOGS_AUTH_DIR", "/home/box/discogs-auth"))
    ok &= check(
        f"DISCOGS_AUTH_DIR exists ({auth_dir})",
        auth_dir.is_dir(),
        "create it and copy personal.env.example; set DISCOGS_AUTH_DIR if elsewhere",
    )
    auth_env = Path(os.environ.get("DISCOGS_AUTH_ENV", auth_dir / "auth.env"))
    has_cookie = auth_env.is_file() and "COOKIE=" in auth_env.read_text()
    ok &= check("auth.env holds COOKIE=", has_cookie, f"missing COOKIE in {auth_env}")
    if probe and has_cookie:
        proc = subprocess.run(
            [sys.executable, str(pack / "discogs-scripts/auth-refresh/scripts/refresh.py"),
             "--check-only"],
            capture_output=True, text=True, timeout=60,
        )
        ok &= check(
            "auth-refresh --check-only",
            proc.returncode == 0 and "ok" in proc.stdout,
            (proc.stdout + proc.stderr).strip().splitlines()[-1][:200]
            if proc.stdout or proc.stderr else "no output",
        )
    return ok


def verify_whatsapp(clone: Path, probe: bool) -> bool:
    ok = True
    pack = clone / "grok_bots" / "whatsapp-bot"
    ok &= check("whatsapp pack present", (pack / "_lib").is_dir())
    ptr = pack / "_auth" / "AUTH_PATH.txt"
    default_jar = Path("/home/box/whatsapp-auth/auth.env")
    jar = Path(ptr.read_text().strip()) if ptr.is_file() else default_jar
    has_cookie = jar.is_file() and "COOKIE=" in jar.read_text()
    ok &= check(
        f"auth jar holds COOKIE= ({jar})",
        has_cookie,
        "QR-link, then run the exporter; see grok_bots/whatsapp-bot/docs/qr-link.md",
    )
    if probe and has_cookie:
        proc = subprocess.run(
            [sys.executable, str(pack / "auth-check/scripts/check.py"), "--no-probe"],
            capture_output=True, text=True, timeout=60, cwd=pack,
        )
        ok &= check(
            "auth-check --no-probe",
            proc.returncode == 0,
            (proc.stdout + proc.stderr).strip().splitlines()[-1][:200]
            if proc.stdout or proc.stderr else "no output",
        )
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bot", choices=["discogs", "whatsapp"], required=True)
    ap.add_argument(
        "--probe",
        action="store_true",
        help="also run the bot's read-only auth probe (needs a live session jar)",
    )
    args = ap.parse_args()

    clone = find_clone()
    if clone is None:
        print("[FAIL] repo clone not found — clone alexhawat/bots-agents-skills "
              "or set BOTS_REPO_ROOT")
        return 1
    print(f"clone: {clone}")

    ok = verify_discogs(clone, args.probe) if args.bot == "discogs" else verify_whatsapp(clone, args.probe)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
