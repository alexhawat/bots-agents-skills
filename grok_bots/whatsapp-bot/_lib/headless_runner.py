"""Shell out to Node headless CDP runner. Never prints cookies/tokens."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "_lib" / "run_headless.mjs"


def run_headless(command: str, args: dict[str, Any] | None = None, extra: list[str] | None = None) -> dict[str, Any]:
    """
    Run NODE_OPTIONS=--experimental-websocket node run_headless.mjs <command> --json-args '...'.
    Returns parsed JSON. Raises SystemExit with runner exit code on failure.
    """
    env = os.environ.copy()
    opts = env.get("NODE_OPTIONS", "")
    if "--experimental-websocket" not in opts:
        env["NODE_OPTIONS"] = (opts + " --experimental-websocket").strip()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":30"

    cmd = ["node", str(RUNNER), command, "--json-args", json.dumps(args or {})]
    if extra:
        cmd.extend(extra)

    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    stdout = (proc.stdout or "").strip()
    data: dict[str, Any]
    if not stdout:
        data = {"ok": False, "error": "empty stdout from run_headless"}
    else:
        # Last JSON line
        line = stdout.splitlines()[-1]
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            data = {"ok": False, "error": "non-json stdout", "raw_len": len(stdout)}
    if proc.returncode != 0:
        print(json.dumps(data), flush=True)
        raise SystemExit(proc.returncode)
    return data
