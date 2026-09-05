#!/usr/bin/env python3
"""Hybrid vinyl photo → Discogs release identify.

No Discogs image-search API. Flow:
  image (optional OCR via tesseract) and/or --query text
  → extract catno/barcode + artist/title hints
  → autocomplete + public search (_lib/discogs_search)
  → optional --check-collection (UserReleaseData)

Grok Bot / vision can supply --query from image Read when OCR is weak.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.discogs_search import (  # noqa: E402
    SearchHit,
    autocomplete,
    check_in_collection,
    extract_tokens,
    lookup_query,
    merge_hits,
    public_search,
    rank_hits,
)
from _lib.errors import DiscogsError, cli_main  # noqa: E402

TASK = Path(__file__).resolve().parents[1]


def ocr_image(path: Path) -> str:
    """Run tesseract if installed; else return empty and note."""
    if not shutil.which("tesseract"):
        return ""
    try:
        proc = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return (proc.stdout or "").strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"# OCR error for {path.name}: {e}", file=sys.stderr)
        return ""


def format_hit(h: SearchHit, idx: int) -> str:
    artists = h.artists or "?"
    year = h.year or "?"
    bits = [f"score={h.score:.0f}", f"via={h.source}"]
    if h.catno:
        bits.append(f"catno={h.catno}")
    if h.country:
        bits.append(h.country)
    if h.formats:
        bits.append(h.formats)
    return (
        f"{idx}. [{h.kind}] id={h.discogs_id}  {artists} — {h.title}  ({year})\n"
        f"   {h.url}\n"
        f"   {' | '.join(bits)}"
    )


def gather_text(images: list[Path], query: str | None) -> tuple[str, list[str]]:
    """Combine OCR + --query; return (combined_text, notes)."""
    notes: list[str] = []
    parts: list[str] = []
    if query:
        parts.append(query.strip())
        notes.append("using --query text")
    has_tesseract = bool(shutil.which("tesseract"))
    if images and not has_tesseract:
        notes.append(
            "tesseract not installed — OCR skipped. "
            "Grok Bot can Read the image and pass --query from vision."
        )
    for img in images:
        if not img.is_file():
            raise DiscogsError(f"Image not found: {img}")
        if has_tesseract:
            text = ocr_image(img)
            if text:
                parts.append(text)
                notes.append(f"OCR from {img.name}: {len(text)} chars")
            else:
                notes.append(f"OCR empty for {img.name}")
        else:
            notes.append(f"image noted (no OCR): {img}")
    combined = "\n".join(parts).strip()
    return combined, notes


def search_from_text(
    text: str,
    auth: dict | None,
    *,
    currency: str,
) -> list[SearchHit]:
    catnos, barcodes, hints = extract_tokens(text)
    hits: list[SearchHit] = []
    prefer = list(catnos) + list(barcodes)

    for b in barcodes:
        hits.extend(lookup_query(b, auth, as_barcode=True, currency=currency))
    for c in catnos:
        hits.extend(lookup_query(c, auth, as_catno=True, currency=currency))

    # Free-text artist/title: autocomplete + public q=
    search_blob = hints or text
    # If we only had tokens, still run full text once
    if search_blob and search_blob not in prefer:
        hits.extend(autocomplete(search_blob, auth, currency=currency))
        hits.extend(public_search(q=search_blob))
        # Also try first ~6 significant words if long OCR dump
        words = [w for w in re.split(r"\s+", search_blob) if len(w) > 2][:8]
        short = " ".join(words)
        if short and short != search_blob:
            hits.extend(autocomplete(short, auth, currency=currency))
            hits.extend(public_search(q=short))

    if not hits and text:
        hits.extend(lookup_query(text, auth, currency=currency))

    merged = merge_hits(hits)
    return rank_hits(merged, query=text, prefer_tokens=prefer)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "images",
        nargs="*",
        type=Path,
        help="Optional image path(s) for OCR",
    )
    ap.add_argument(
        "--query",
        "-q",
        help="Text query (from vision / user). Required if no usable OCR.",
    )
    ap.add_argument(
        "--check-collection",
        action="store_true",
        help="Mark each Release hit in-collection yes/no via UserReleaseData",
    )
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--limit", type=int, default=15)
    args = ap.parse_args()

    if not args.images and not args.query:
        ap.error("Provide image path(s) and/or --query")

    combined, notes = gather_text(list(args.images or []), args.query)
    print("# vinyl-photo-identify (hybrid)")
    for n in notes:
        print(f"# note: {n}")

    if not combined:
        print(
            "# No text to search. Install tesseract or pass --query "
            "(Grok Bot vision Read → --query)."
        )
        raise SystemExit(2)

    catnos, barcodes, hints = extract_tokens(combined)
    print(f"# extracted catnos={catnos or '-'} barcodes={barcodes or '-'} "
          f"hints={hints[:80]!r}{'…' if len(hints) > 80 else ''}")

    auth = None
    if args.check_collection:
        auth = load_auth(task_root=TASK)
    else:
        try:
            auth = load_auth(task_root=TASK)
        except DiscogsError:
            auth = None

    hits = search_from_text(combined, auth, currency=args.currency)
    if not hits:
        print("No candidates.")
        raise SystemExit(1)

    print(f"# candidates={len(hits)} (showing up to {args.limit})")
    for i, h in enumerate(hits[: max(1, args.limit)], 1):
        print(format_hit(h, i))
        if args.check_collection and h.is_release and auth:
            info = check_in_collection(auth, h.discogs_id)
            if info["viewer_null"] and not info["in_collection"]:
                print("   in-collection: unknown (viewer=null)")
            else:
                yn = "yes" if info["in_collection"] else "no"
                print(f"   in-collection: {yn}  copies={info['copies']}")


if __name__ == "__main__":
    cli_main(main)
