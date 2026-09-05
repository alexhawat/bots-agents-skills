#!/usr/bin/env python3
"""Compare a HAR or curls.txt against expected GraphQL operation→sha fixtures.

Reports matched ops, drifted hashes, new ops, and missing expected ops.
Exit 0 if no hash drift on known names; exit 1 if any known name has a different hash.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = TASK / "fixtures" / "known-operations.json"

# operationName=… in query string or JSON body
OP_RE = re.compile(
    r"""["']?operationName["']?\s*[:=]\s*["']([A-Za-z0-9_]+)["']""",
    re.I,
)
# sha256Hash in URL-encoded or raw JSON
SHA_RE = re.compile(
    r"""["']?sha256Hash["']?\s*[:=]\s*["']([a-fA-F0-9]{64})["']""",
    re.I,
)
# URL-encoded extensions=...sha256Hash%22%3A%22HASH
SHA_URL_RE = re.compile(
    r"sha256Hash(?:%22%3A%22|%22:%22|\"\s*:\s*\")([a-fA-F0-9]{64})",
    re.I,
)
OP_URL_RE = re.compile(
    r"operationName(?:=|%3D)([A-Za-z0-9_]+)",
    re.I,
)


def load_fixture(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    ops = data.get("operations") or data
    if not isinstance(ops, dict):
        raise SystemExit(f"fixture {path}: expected operations object")
    return {str(k): str(v).lower() for k, v in ops.items()}


def _extract_from_text(text: str) -> dict[str, set[str]]:
    """Map operationName → set of sha256 hashes found near it / in same chunk."""
    found: dict[str, set[str]] = {}

    # Prefer structured JSON bodies in --data-raw / postData
    for m in re.finditer(
        r"""\{[^{}]*"operationName"\s*:\s*"([A-Za-z0-9_]+)"[^{}]*\}""",
        text,
        re.S,
    ):
        chunk = m.group(0)
        op = m.group(1)
        sha_m = SHA_RE.search(chunk)
        if sha_m:
            found.setdefault(op, set()).add(sha_m.group(1).lower())

    # Also scan line-by-line / URL params (GET persisted queries)
    for line in text.splitlines():
        if "graphql" not in line.lower() and "operationName" not in line and "sha256Hash" not in line:
            # still allow comment lines that name ops without hashes
            ops_only = OP_RE.findall(line) or OP_URL_RE.findall(line)
            for op in ops_only:
                found.setdefault(op, set())
            continue

        decoded = line
        try:
            decoded = urllib.parse.unquote(line)
        except Exception:
            pass

        ops = OP_RE.findall(decoded) or OP_URL_RE.findall(line)
        shas = [s.lower() for s in (SHA_RE.findall(decoded) + SHA_URL_RE.findall(line))]
        if not ops and not shas:
            continue
        if len(ops) == 1 and shas:
            found.setdefault(ops[0], set()).update(shas)
        elif ops and shas:
            # pair first op with first sha when multiple on one line
            found.setdefault(ops[0], set()).add(shas[0])
            for op in ops[1:]:
                found.setdefault(op, set())
        elif ops:
            for op in ops:
                found.setdefault(op, set())
        # lone shas ignored without op

    return found


def extract_from_curls(path: Path) -> dict[str, set[str]]:
    return _extract_from_text(path.read_text(errors="replace"))


def extract_from_har(path: Path) -> dict[str, set[str]]:
    raw = path.read_text(errors="replace")
    try:
        har = json.loads(raw)
    except json.JSONDecodeError:
        # fall back to text scrape
        return _extract_from_text(raw)

    found: dict[str, set[str]] = {}
    entries = ((har.get("log") or {}).get("entries")) or []
    for entry in entries:
        req = entry.get("request") or {}
        url = req.get("url") or ""
        chunks = [url]
        post = req.get("postData") or {}
        if post.get("text"):
            chunks.append(post["text"])
        for q in req.get("queryString") or []:
            chunks.append(f"{q.get('name')}={q.get('value')}")
        blob = "\n".join(chunks)
        partial = _extract_from_text(blob)
        for op, shas in partial.items():
            found.setdefault(op, set()).update(shas)
    return found


def extract_ops(path: Path) -> dict[str, set[str]]:
    name = path.name.lower()
    if name.endswith(".har"):
        return extract_from_har(path)
    return extract_from_curls(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="HAR file or curls.txt to compare")
    ap.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help=f"known-operations.json (default: {DEFAULT_FIXTURE})",
    )
    args = ap.parse_args()

    if not args.path.is_file():
        raise SystemExit(f"not found: {args.path}")
    if not args.fixture.is_file():
        raise SystemExit(f"fixture not found: {args.fixture}")

    expected = load_fixture(args.fixture)
    observed = extract_ops(args.path)

    matched: list[str] = []
    drifted: list[tuple[str, str, str]] = []  # name, expected, observed
    new_ops: list[str] = []
    missing: list[str] = []

    for name, exp_sha in sorted(expected.items()):
        if name not in observed:
            missing.append(name)
            continue
        shas = observed[name]
        if not shas:
            # op named but no hash in capture (e.g. PLACEHOLDER curls)
            missing.append(f"{name} (named, no hash in capture)")
            continue
        if exp_sha in shas and len(shas) == 1:
            matched.append(name)
        elif exp_sha in shas:
            matched.append(name)
            # also other hashes?
            others = shas - {exp_sha}
            if others:
                drifted.append((name, exp_sha, ",".join(sorted(others))))
        else:
            drifted.append((name, exp_sha, ",".join(sorted(shas))))

    for name in sorted(observed):
        if name not in expected:
            new_ops.append(name)

    print(f"# har-diff input={args.path} fixture={args.fixture}")
    print(f"matched ({len(matched)}):")
    for n in matched:
        print(f"  ok {n} = {expected[n][:12]}…")
    print(f"drifted ({len(drifted)}):")
    for n, exp, obs in drifted:
        print(f"  DRIFT {n}: expected={exp} observed={obs}")
    print(f"new ops ({len(new_ops)}):")
    for n in new_ops:
        shas = observed[n]
        sha_s = ",".join(sorted(shas)) if shas else "(no hash)"
        print(f"  + {n} sha={sha_s}")
    print(f"missing expected ({len(missing)}):")
    for n in missing:
        print(f"  - {n}")

    if drifted:
        print("# result: FAIL (hash drift on known operations)")
        return 1
    print("# result: OK (no hash drift on known names)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
