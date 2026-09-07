"""Shared KEY=VALUE env-file parser.

Byte-identical copy lives in both bot packs — the box install copies only one
pack subtree, so this file is duplicated rather than imported from a common
directory. A test in each pack fails if the two copies drift apart.
"""
from __future__ import annotations

from pathlib import Path


def parse_env(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines; skip blanks/comments; strip surrounding quotes.

    Splits on the first '=' only — cookie jars are full of '='.
    """
    out: dict[str, str] = {}
    path = Path(path)
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def merge_env(*paths: Path) -> dict[str, str]:
    """Parse each file in order and merge; later files win."""
    merged: dict[str, str] = {}
    for path in paths:
        merged.update(parse_env(path))
    return merged
