"""HTTP helpers for Discogs session requests. Never log Cookie values."""
from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def _build_headers(
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    accept: str = "*/*",
    apollo: bool = False,
) -> dict[str, str]:
    out: dict[str, str] = {
        "accept": accept,
        "accept-encoding": "identity",
        "user-agent": auth.get("USER_AGENT", DEFAULT_UA),
        "cookie": auth["COOKIE"],
        "referer": "https://www.discogs.com/",
    }
    if auth.get("AUTHORIZATION"):
        out["authorization"] = auth["AUTHORIZATION"]
    if apollo:
        out["apollographql-client-name"] = auth.get(
            "APOLLO_CLIENT_NAME", "release-page-client"
        )
        out["content-type"] = "application/json"
    if headers:
        # Caller overrides (but never strip cookie unless explicitly replaced)
        out.update(headers)
    return out


def get_bytes(
    url: str,
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    apollo: bool = False,
    timeout: int = 60,
) -> bytes:
    req_headers = _build_headers(auth, headers, apollo=apollo)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            return data
    except urllib.error.HTTPError as e:
        body = e.read()[:800]
        # Never include request Cookie in error text
        raise SystemExit(f"HTTP {e.code} for {url.split('?', 1)[0]}: {body!r}") from e


def get_text(
    url: str,
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    apollo: bool = False,
    timeout: int = 60,
) -> str:
    return get_bytes(url, auth, headers, apollo=apollo, timeout=timeout).decode(
        "utf-8", errors="replace"
    )


def get_json(
    url: str,
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    apollo: bool = False,
    timeout: int = 60,
) -> Any:
    h = {"accept": "application/json"}
    if headers:
        h.update(headers)
    text = get_text(url, auth, h, apollo=apollo, timeout=timeout)
    return json.loads(text)


def get_public_json(url: str, user_agent: str | None = None, timeout: int = 60) -> Any:
    """Unauthenticated Discogs public API (User-Agent only)."""
    headers = {
        "accept": "application/json",
        "user-agent": user_agent or DEFAULT_UA,
        "accept-encoding": "identity",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read()[:800]
        raise SystemExit(f"HTTP {e.code} for {url}: {body!r}") from e


def graphql_get(
    auth: dict[str, str],
    *,
    endpoint: str,
    operation_name: str,
    sha256_hash: str,
    variables: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> Any:
    """GET a Discogs persisted GraphQL query (Apollo). Never logs Cookie."""
    params = {
        "operationName": operation_name,
        "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps(
            {"persistedQuery": {"version": 1, "sha256Hash": sha256_hash}},
            separators=(",", ":"),
        ),
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    extra = {
        "accept": "application/json",
        "content-type": "application/json",
        "apollographql-client-name": auth.get(
            "APOLLO_CLIENT_NAME", "release-page-client"
        ),
    }
    if headers:
        extra.update(headers)
    return get_json(url, auth, extra, timeout=timeout)
