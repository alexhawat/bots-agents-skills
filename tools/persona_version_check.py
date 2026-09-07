#!/usr/bin/env python3
"""Persona version sync check.

Each bot's persona carries a `// version` marker (e.g. `// version 1.2`, or a
`// version` line followed by the number on the next line). Every pack that
ships a persona for the same bot MUST carry the same version, so a capability
or auth change on the canonical grok persona forces the hermes pack to move in
the same commit.

Checks every PERSONA.md under grok_bots/, hermes/, and openclaw/ grouped by bot
slug (parent directory name). Exits 1 listing mismatches. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREES = ("grok_bots", "hermes", "openclaw")
MARKER = re.compile(r"^//\s*version\s*(?:\n\s*(\S+)|(\S+))?", re.MULTILINE)


def persona_version(path: Path) -> str | None:
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^//\s*version\s*(.*)$", line.strip())
        if m:
            inline = m.group(1).strip().split(" ")[0].split("—")[0].strip()
            if inline and re.match(r"^\d", inline):
                return inline
            for follow in lines[i + 1 :]:
                follow = follow.strip()
                if follow:
                    return follow.split(" ")[0].split("—")[0].strip()
    return None


def main() -> int:
    by_bot: dict[str, list[tuple[Path, str | None]]] = {}
    for tree in TREES:
        base = ROOT / tree
        if not base.is_dir():
            continue
        for persona in sorted(base.glob("*/PERSONA.md")):
            by_bot.setdefault(persona.parent.name, []).append(
                (persona, persona_version(persona))
            )

    failures: list[str] = []
    for bot, entries in sorted(by_bot.items()):
        versions = {v for _, v in entries}
        if len(versions) > 1:
            failures.append(bot)
            print(f"version mismatch for {bot}:", file=sys.stderr)
            for path, version in entries:
                print(f"  {path.relative_to(ROOT)}: {version}", file=sys.stderr)
    if failures:
        print(
            "Bump the `// version` marker in every pack persona for the bot, "
            "in the same commit.",
            file=sys.stderr,
        )
        return 1
    print("ok: persona versions in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
