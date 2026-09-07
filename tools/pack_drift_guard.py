"""Reference-not-copy guard for the hermes/ and openclaw/ agent packs.

Policy: the canonical runnable scripts live only under grok_bots/<bot>/.
The hermes/ and openclaw/ packs are instructions (markdown/yaml) that point at
those scripts — they must never carry their own copies. Drift happens when
someone copies a .py/.mjs/.cjs file into a pack instead of referencing it.

This script exits 1 and prints the offending paths if any tracked file under
hermes/ or openclaw/ ends in .py, .mjs, or .cjs. Stdlib only.
"""

import subprocess
import sys

PACK_DIRS = ("hermes", "openclaw")
BANNED_SUFFIXES = (".py", ".mjs", ".cjs")


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "--"] + list(PACK_DIRS),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def main():
    offenders = [
        path
        for path in tracked_files()
        if path.endswith(BANNED_SUFFIXES)
    ]
    if offenders:
        print(
            "pack drift: executable code is tracked under "
            + "/".join(PACK_DIRS)
            + " — reference grok_bots/ scripts, never copy them:"
        )
        for path in offenders:
            print(f"  {path}")
        return 1
    print("ok: hermes/ and openclaw/ contain instructions only (no .py/.mjs/.cjs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
