"""Shared Discogs catalog search: site autocomplete + public database/search.

Never logs Cookie / secrets. Autocomplete may use session Cookie when present;
public API uses User-Agent only (documented).
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Iterable

from _lib.http import DEFAULT_UA, get_json, get_public_json, graphql_get

AUTOCOMPLETE_URL = (
    "https://www.discogs.com/service/search-component/public/api/autocomplete"
)
PUBLIC_SEARCH_URL = "https://api.discogs.com/database/search"
GRAPHQL = "https://www.discogs.com/service/catalog/api/graphql"
USER_RELEASE_SHA = (
    "a5c6a6cf7e06b6a9d43ab71e49f9e0e4ecb0f204d0db43a63d0f279075bd06e4"
)
PUBLIC_UA = "DiscogsScripts/1.0"

# Catno-ish: letters+digits with optional dashes/spaces; barcodes mostly digits
_TOKEN_RE = re.compile(
    r"(?i)\b("
    r"[A-Z]{1,6}[- ]?\d{2,7}(?:[- ]?\d{1,5})?"  # DMO-55454, ABC 1234
    r"|\d{8,14}"  # EAN/UPC-ish
    r")\b"
)
_NOISE = re.compile(r"[^\w\s\-./]+", re.UNICODE)


@dataclass
class SearchHit:
    """Normalized release/master/artist/label hit from either search source."""

    kind: str  # Release | MasterRelease | Artist | Label | release | master | ...
    discogs_id: int
    title: str
    artists: str = ""
    year: str = ""
    country: str = ""
    catno: str = ""
    url: str = ""
    formats: str = ""
    source: str = ""  # autocomplete | public
    score: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def is_release(self) -> bool:
        k = (self.kind or "").lower()
        return k in ("release",) or self.kind == "Release"


def _artist_blob_from_primary(primary: list[dict] | None) -> str:
    parts: list[str] = []
    for pa in primary or []:
        name = (
            pa.get("displayName")
            or (pa.get("artist") or {}).get("name")
            or ""
        )
        if name:
            parts.append(str(name))
    return " / ".join(parts)


def _format_blob(formats: list[dict] | None) -> str:
    bits: list[str] = []
    for fmt in formats or []:
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


def _site_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return "https://www.discogs.com" + path


def hit_from_autocomplete(item: dict[str, Any]) -> SearchHit:
    typename = item.get("__typename") or ""
    did = int(item.get("discogsId") or 0)
    if typename == "MasterRelease":
        key = item.get("keyRelease") or {}
        title = key.get("title") or item.get("title") or ""
        artists = _artist_blob_from_primary(key.get("primaryArtists"))
        year = str(key.get("released") or "")
        formats = ""
        country = ""
    else:
        title = item.get("title") or ""
        artists = _artist_blob_from_primary(item.get("primaryArtists"))
        year = str(item.get("released") or "")
        formats = _format_blob(item.get("formats"))
        country = item.get("country") or ""
    return SearchHit(
        kind=typename or "unknown",
        discogs_id=did,
        title=title,
        artists=artists,
        year=year,
        country=country,
        url=_site_url(item.get("siteUrl")),
        formats=formats,
        source="autocomplete",
        raw=item,
    )


def hit_from_public(item: dict[str, Any]) -> SearchHit:
    uri = item.get("uri") or ""
    title = item.get("title") or ""
    # Public search often "Artist - Title"
    artists = ""
    if " - " in title:
        artists, title_rest = title.split(" - ", 1)
        title = title_rest
    barcodes = item.get("barcode") or []
    if isinstance(barcodes, list):
        barcode_s = ", ".join(str(b) for b in barcodes if b)
    else:
        barcode_s = str(barcodes) if barcodes else ""
    return SearchHit(
        kind=str(item.get("type") or "release"),
        discogs_id=int(item.get("id") or 0),
        title=title,
        artists=artists.strip(),
        year=str(item.get("year") or ""),
        country=item.get("country") or "",
        catno=item.get("catno") or barcode_s,
        url=_site_url(uri),
        formats=", ".join(item.get("format") or [])
        if isinstance(item.get("format"), list)
        else str(item.get("format") or ""),
        source="public",
        raw=item,
    )


def autocomplete(
    query: str,
    auth: dict[str, str] | None = None,
    *,
    currency: str = "EUR",
    search_type: str = "MASTER,RELEASE,ARTIST,LABEL",
) -> list[SearchHit]:
    """Site autocomplete (captured barcode.har). Works with or without Cookie."""
    q = (query or "").strip()
    if not q:
        return []
    params = {
        "search": q,
        "search_type": search_type,
        "currency": currency,
    }
    url = f"{AUTOCOMPLETE_URL}?{urllib.parse.urlencode(params)}"
    if auth and auth.get("COOKIE"):
        data = get_json(url, auth)
    else:
        data = get_public_json(url, user_agent=PUBLIC_UA)
    return [hit_from_autocomplete(x) for x in (data.get("autocomplete") or [])]


def public_search(
    *,
    catno: str | None = None,
    barcode: str | None = None,
    q: str | None = None,
    type_: str = "release",
    per_page: int = 25,
) -> list[SearchHit]:
    """Documented public database/search (User-Agent DiscogsScripts/1.0)."""
    params: dict[str, str] = {"type": type_, "per_page": str(per_page)}
    if barcode:
        params["barcode"] = barcode.strip()
    elif catno:
        params["catno"] = catno.strip()
    elif q:
        params["q"] = q.strip()
    else:
        return []
    url = f"{PUBLIC_SEARCH_URL}?{urllib.parse.urlencode(params)}"
    data = get_public_json(url, user_agent=PUBLIC_UA)
    return [hit_from_public(x) for x in (data.get("results") or [])]


def looks_like_barcode(token: str) -> bool:
    t = re.sub(r"[\s\-]", "", token or "")
    return bool(re.fullmatch(r"\d{8,14}", t))


def looks_like_catno(token: str) -> bool:
    t = (token or "").strip()
    if looks_like_barcode(t):
        return False
    return bool(re.fullmatch(r"(?i)[A-Z0-9][A-Z0-9.\- ]{1,20}\d[A-Z0-9.\- ]*", t))


def extract_tokens(text: str) -> tuple[list[str], list[str], str]:
    """Return (catnos, barcodes, free_text_hints) from OCR / query string."""
    raw = (text or "").strip()
    if not raw:
        return [], [], ""
    catnos: list[str] = []
    barcodes: list[str] = []
    seen: set[str] = set()
    for m in _TOKEN_RE.finditer(raw):
        tok = re.sub(r"\s+", "-", m.group(1).strip())
        key = tok.upper()
        if key in seen:
            continue
        seen.add(key)
        if looks_like_barcode(tok):
            barcodes.append(re.sub(r"[\s\-]", "", tok))
        else:
            catnos.append(tok.upper() if "-" in tok or tok.isalnum() else tok)
    # Free-text: drop matched tokens for artist/title hints
    hints = raw
    for m in _TOKEN_RE.finditer(raw):
        hints = hints.replace(m.group(0), " ")
    hints = _NOISE.sub(" ", hints)
    hints = re.sub(r"\s+", " ", hints).strip()
    return catnos, barcodes, hints


def merge_hits(hits: Iterable[SearchHit]) -> list[SearchHit]:
    """Dedupe by (kind_norm, id); prefer autocomplete Release over public."""
    best: dict[tuple[str, int], SearchHit] = {}
    for h in hits:
        if not h.discogs_id:
            continue
        kind_n = "release" if h.is_release else (h.kind or "").lower()
        key = (kind_n, h.discogs_id)
        prev = best.get(key)
        if prev is None or (h.source == "autocomplete" and prev.source != "autocomplete"):
            best[key] = h
        elif prev and not prev.artists and h.artists:
            prev.artists = h.artists
        elif prev and not prev.catno and h.catno:
            prev.catno = h.catno
        if prev and h.source == "public" and h.catno and not best[key].catno:
            best[key].catno = h.catno
    return list(best.values())


def rank_hits(
    hits: list[SearchHit],
    *,
    query: str = "",
    prefer_tokens: list[str] | None = None,
) -> list[SearchHit]:
    """Score releases highest, then masters; boost token / query overlap."""
    q = (query or "").lower()
    tokens = [t.lower() for t in (prefer_tokens or []) if t]

    def score(h: SearchHit) -> float:
        s = 0.0
        if h.is_release:
            s += 100
        elif (h.kind or "").lower() in ("masterrelease", "master"):
            s += 50
        elif (h.kind or "").lower() in ("artist",):
            s += 10
        else:
            s += 5
        blob = " ".join(
            [h.title, h.artists, h.catno, h.year, h.country]
        ).lower()
        for t in tokens:
            if t and t in blob:
                s += 30
            if t and h.catno and t.replace("-", "") == h.catno.replace("-", "").lower():
                s += 40
        if q:
            for word in q.split():
                if len(word) > 2 and word in blob:
                    s += 5
        if h.source == "autocomplete":
            s += 2
        h.score = s
        return s

    ranked = sorted(hits, key=score, reverse=True)
    return ranked


def lookup_query(
    query: str,
    auth: dict[str, str] | None = None,
    *,
    as_barcode: bool = False,
    as_catno: bool = False,
    currency: str = "EUR",
) -> list[SearchHit]:
    """Run autocomplete + public search for a catno/barcode/free query."""
    q = (query or "").strip()
    if not q:
        return []
    hits: list[SearchHit] = []
    hits.extend(autocomplete(q, auth, currency=currency))

    if as_barcode or looks_like_barcode(q):
        hits.extend(public_search(barcode=re.sub(r"[\s\-]", "", q)))
    elif as_catno or looks_like_catno(q):
        hits.extend(public_search(catno=q))
        # Also try q= in case catno param is strict
        hits.extend(public_search(q=q))
    else:
        # Free text: try as catno if token-like, else q=
        catnos, barcodes, _hints = extract_tokens(q)
        for b in barcodes:
            hits.extend(public_search(barcode=b))
        for c in catnos:
            hits.extend(public_search(catno=c))
        hits.extend(public_search(q=q))

    prefer = [q]
    if as_barcode or looks_like_barcode(q):
        prefer.append(re.sub(r"[\s\-]", "", q))
    merged = merge_hits(hits)
    return rank_hits(merged, query=q, prefer_tokens=prefer)


def check_in_collection(auth: dict[str, str], release_id: int) -> dict[str, Any]:
    """UserReleaseData GraphQL — same sha as price-suggest. Never logs Cookie."""
    data = graphql_get(
        auth,
        endpoint=GRAPHQL,
        operation_name="UserReleaseData",
        sha256_hash=USER_RELEASE_SHA,
        variables={"discogsId": int(release_id)},
    )
    release = (data.get("data") or {}).get("release") or {}
    viewer = (data.get("data") or {}).get("viewer")
    coll = release.get("collectionItems") or {}
    edges = coll.get("edges") or []
    total = coll.get("totalCount")
    if total is None:
        total = len(edges)
    return {
        "in_collection": bool(edges) or (isinstance(total, int) and total > 0),
        "copies": total if isinstance(total, int) else len(edges),
        "viewer_null": viewer is None,
        "in_wantlist": release.get("inWantlist"),
        "edges": edges,
    }
