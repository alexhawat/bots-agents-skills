"""Minimal CLI helpers for WhatsApp scripts. Never print cookie/token values."""
from __future__ import annotations

import argparse
import sys
from typing import NoReturn


def add_auth_args(ap: argparse.ArgumentParser) -> None:
    """Optional common flags (scripts still load via _lib.auth)."""
    ap.add_argument(
        "--no-probe",
        action="store_true",
        help="Skip optional weak HTTP probe when the script supports one",
    )


def die(msg: str, code: int = 1) -> NoReturn:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def ok(msg: str) -> None:
    print(msg)
