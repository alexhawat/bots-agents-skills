#!/usr/bin/env python3
"""Run a JSON/YAML batch of read-only WhatsApp scripts via subprocess."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# slug -> script relative to ROOT
READ_ONLY = {
    "auth-check": "auth-check/scripts/check.py",
    "chats-list": "chats-list/scripts/list_chats.py",
    "messages-read": "messages-read/scripts/read_messages.py",
    "chats-search": "chats-search/scripts/search_chats.py",
    "contact-info": "contact-info/scripts/info.py",
    "media-download": "media-download/scripts/download.py",
    "har-diff": "har-diff/scripts/diff.py",
}

BLOCKED = {"message-send", "message-mark-read", "qr-link", "auth-export"}


def load_batch(path: Path) -> dict:
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError:
            # minimal YAML for our fixture shape: name + jobs list with slug/args
            return _minimal_yaml(text)
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise SystemExit("batch file must be an object with jobs[]")
    return data


def _minimal_yaml(text: str) -> dict:
    """Tiny subset parser for fixtures if PyYAML missing."""
    name = "batch"
    jobs: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        raw = line.rstrip()
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if raw.startswith("name:"):
            name = raw.split(":", 1)[1].strip()
        elif raw.strip().startswith("- slug:"):
            if cur:
                jobs.append(cur)
            cur = {"slug": raw.split(":", 1)[1].strip(), "args": []}
        elif cur is not None and "args:" in raw and "[" in raw:
            inside = raw.split("[", 1)[1].rsplit("]", 1)[0]
            parts = [p.strip().strip('"').strip("'") for p in inside.split(",") if p.strip()]
            cur["args"] = parts
        elif cur is not None and raw.strip().startswith("- ") and "slug" not in raw:
            pass
    if cur:
        jobs.append(cur)
    return {"name": name, "jobs": jobs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("batch", type=Path, help="JSON or YAML batch file")
    args = ap.parse_args()

    if not args.batch.is_file():
        print(f"not found: {args.batch}", file=sys.stderr)
        return 1

    data = load_batch(args.batch)
    jobs = data.get("jobs") or []
    print(f"# batch name={data.get('name', args.batch.name)} jobs={len(jobs)}")

    import subprocess

    rc_all = 0
    for i, job in enumerate(jobs):
        if not isinstance(job, dict):
            print(f"# skip invalid job[{i}]", file=sys.stderr)
            rc_all = rc_all or 1
            continue
        slug = job.get("slug")
        if slug in BLOCKED:
            print(f"# blocked mutating/runbook slug={slug}", file=sys.stderr)
            rc_all = rc_all or 2
            continue
        if slug not in READ_ONLY:
            print(f"# unknown slug={slug}", file=sys.stderr)
            rc_all = rc_all or 1
            continue
        script = ROOT / READ_ONLY[slug]
        if not script.is_file():
            print(f"# missing {script}", file=sys.stderr)
            rc_all = rc_all or 1
            continue
        job_args = job.get("args") or []
        if not isinstance(job_args, list):
            job_args = []
        cmd = [sys.executable, str(script), *[str(a) for a in job_args]]
        print(f"# invoked {script} args={job_args}")
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            rc_all = rc_all or proc.returncode
            print(f"# child exit={proc.returncode}")

    print(f"# batch done exit={rc_all}")
    return rc_all


if __name__ == "__main__":
    raise SystemExit(main())
