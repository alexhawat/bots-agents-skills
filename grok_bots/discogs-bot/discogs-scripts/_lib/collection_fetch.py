"""Paginate ViewerCollectionListData (captured collection-search 2026-09-05).

Uses only the persisted query sha256Hash from the live capture — no invented fields.
Never logs Cookie values.
"""
from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import Any

from _lib.errors import DiscogsAPIError, DiscogsAuthError
from _lib.http import graphql_get

ENDPOINT = "https://www.discogs.com/service/catalog/api/graphql"
OPERATION = "ViewerCollectionListData"
# From collection-search/capture/collection-federico.har (verified live)
SHA256 = "ebc71d10939729462ee62c506326081612eccc8c93ea595d638b4af123835f1b"

CSV_COLUMNS = [
    "collection_item_id",
    "release_id",
    "title",
    "artists",
    "year",
    "format",
    "label",
    "catno",
    "folder",
    "added_at",
    "url",
]


def artist_blob(release: dict) -> str:
    parts: list[str] = []
    for pa in release.get("primaryArtists") or []:
        name = pa.get("displayName") or (pa.get("artist") or {}).get("name") or ""
        if name:
            parts.append(name)
    return " / ".join(parts)


def format_blob(release: dict) -> str:
    bits: list[str] = []
    for fmt in release.get("formats") or []:
        name = fmt.get("name") or ""
        qty = fmt.get("quantity") or "1"
        desc = ", ".join(fmt.get("description") or [])
        if qty not in ("1", 1, None, ""):
            bits.append(f"{qty} x {name}" if name else str(qty))
        elif name:
            bits.append(name)
        if desc:
            bits.append(desc)
    return " — ".join(bits) if bits else ""


def format_match_blob(release: dict) -> str:
    """Lowercased name + description text for substring format filters."""
    parts: list[str] = []
    for fmt in release.get("formats") or []:
        if fmt.get("name"):
            parts.append(str(fmt["name"]))
        for d in fmt.get("description") or []:
            parts.append(str(d))
        if fmt.get("text"):
            parts.append(str(fmt["text"]))
    return " ".join(parts).lower()


def primary_label_catno(release: dict) -> tuple[str, str]:
    """First LABEL-role relationship (else first label); catalogNumber from that row."""
    labels = release.get("labels") or []
    chosen = None
    for lr in labels:
        if (lr.get("labelRole") or "").upper() == "LABEL":
            chosen = lr
            break
    if chosen is None and labels:
        chosen = labels[0]
    if not chosen:
        return "", ""
    name = ((chosen.get("label") or {}).get("name")) or ""
    catno = chosen.get("catalogNumber") or ""
    if catno in (None, "none"):
        catno = ""
    return name, str(catno)


def year_int(released: Any) -> int | None:
    if released is None or released == "":
        return None
    s = str(released).strip()
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4])
    return None


def item_to_row(it: dict) -> dict[str, Any]:
    rel = it.get("release") or {}
    discogs_id = rel.get("discogsId")
    site = rel.get("siteUrl") or (f"/release/{discogs_id}" if discogs_id else "")
    if site.startswith("/"):
        site = "https://www.discogs.com" + site
    label, catno = primary_label_catno(rel)
    return {
        "collection_item_id": it.get("discogsId"),
        "release_id": discogs_id,
        "title": rel.get("title") or "",
        "artists": artist_blob(rel),
        "year": rel.get("released") or "",
        "format": format_blob(rel),
        "label": label,
        "catno": catno,
        "folder": (it.get("folder") or {}).get("name") or "",
        "added_at": it.get("addedAt") or "",
        "url": site,
        # raw for filters that need formats list
        "_release": rel,
    }


def fetch_page(
    auth: dict[str, str],
    *,
    page: int = 1,
    per_page: int = 50,
    folder_id: int = 0,
    search: str = "",
    currency: str = "EUR",
    direction: str = "DESC",
    field: str = "ADDED",
) -> tuple[list[dict], int | None]:
    """Return (collectionItems, totalCount) for one page."""
    variables = {
        "page": page,
        "perPage": per_page,
        "currency": currency,
        "folderId": folder_id,
        "direction": direction,
        "field": field,
        "search": search,
    }
    data = graphql_get(
        auth,
        endpoint=ENDPOINT,
        operation_name=OPERATION,
        sha256_hash=SHA256,
        variables=variables,
    )
    # Check errors BEFORE viewer: a genuine GraphQL error also nulls viewer,
    # and reporting it as "session dead" sends you down the wrong path.
    if data.get("errors"):
        # Surface GraphQL errors without dumping auth
        raise DiscogsAPIError(f"GraphQL errors: {data['errors']!r}")
    viewer = (data.get("data") or {}).get("viewer")
    if viewer is None:
        raise DiscogsAuthError(
            "viewer=null — session dead or COOKIE incomplete. "
            "Run auth-refresh/scripts/refresh.py --check-only"
        )
    off = viewer.get("offsetCollectionItems") or {}
    items = off.get("collectionItems") or []
    total = off.get("totalCount")
    return items, total


def iter_collection_items(
    auth: dict[str, str],
    *,
    per_page: int = 50,
    folder_id: int = 0,
    search: str = "",
    currency: str = "EUR",
    limit: int | None = None,
    progress: bool = True,
) -> Iterator[dict]:
    """Yield raw collection items until totalCount (or limit)."""
    page = 1
    seen = 0
    total: int | None = None
    while True:
        batch, page_total = fetch_page(
            auth,
            page=page,
            per_page=per_page,
            folder_id=folder_id,
            search=search,
            currency=currency,
        )
        if total is None:
            total = page_total
            if progress:
                print(
                    f"# totalCount={total} search={search!r} folderId={folder_id}",
                    file=sys.stderr,
                )
        if not batch:
            break
        for it in batch:
            yield it
            seen += 1
            if limit is not None and seen >= limit:
                return
        if total is not None and seen >= total:
            break
        page += 1
        if page > 500:
            raise DiscogsAPIError("pagination safety stop (page>500)")


def fetch_rows(
    auth: dict[str, str],
    *,
    per_page: int = 50,
    folder_id: int = 0,
    search: str = "",
    currency: str = "EUR",
    limit: int | None = None,
    progress: bool = True,
) -> list[dict[str, Any]]:
    """Fetch and normalize to CSV-shaped rows (plus private _release)."""
    rows: list[dict[str, Any]] = []
    for it in iter_collection_items(
        auth,
        per_page=per_page,
        folder_id=folder_id,
        search=search,
        currency=currency,
        limit=limit,
        progress=progress,
    ):
        rows.append(item_to_row(it))
    return rows


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    """Strip private keys for JSON/CSV export."""
    return {k: row.get(k, "") for k in CSV_COLUMNS}
