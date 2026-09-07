"""HTTP helpers for Discogs session requests. Never log Cookie values."""
from __future__ import annotations

import gzip
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from _lib.errors import DiscogsHTTPError

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)

# Cap on any single retry wait so a hostile Retry-After can't stall a run.
MAX_RETRY_WAIT = 30.0


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


def _retry_wait(attempt: int, retry_after: str | None) -> float:
    """Seconds to wait before retry ``attempt``: Retry-After if given and
    numeric, else exponential backoff (1s, 2s, 4s, ...) with jitter. Capped."""
    if retry_after:
        try:
            return min(float(retry_after), MAX_RETRY_WAIT)
        except ValueError:
            pass
    return min(2.0**attempt + random.uniform(0, 0.5), MAX_RETRY_WAIT)


def get_bytes(
    url: str,
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    apollo: bool = False,
    timeout: int = 60,
    retries: int = 3,
) -> bytes:
    req_headers = _build_headers(auth, headers, apollo=apollo)
    attempts = max(1, retries)
    for attempt in range(attempts):
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
            retryable = e.code == 429 or e.code >= 500
            if retryable and attempt < attempts - 1:
                wait = _retry_wait(attempt, e.headers.get("Retry-After") if e.headers else None)
                time.sleep(wait)
                continue
            # Never include request Cookie in error text
            raise DiscogsHTTPError(e.code, url.split('?', 1)[0], body) from e
    raise DiscogsHTTPError(0, url.split('?', 1)[0], b"")  # pragma: no cover — unreachable


def get_text(
    url: str,
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    apollo: bool = False,
    timeout: int = 60,
    retries: int = 3,
) -> str:
    return get_bytes(url, auth, headers, apollo=apollo, timeout=timeout, retries=retries).decode(
        "utf-8", errors="replace"
    )


def get_json(
    url: str,
    auth: dict[str, str],
    headers: dict[str, str] | None = None,
    *,
    apollo: bool = False,
    timeout: int = 60,
    retries: int = 3,
) -> Any:
    h = {"accept": "application/json"}
    if headers:
        h.update(headers)
    text = get_text(url, auth, h, apollo=apollo, timeout=timeout, retries=retries)
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
        # Never include request Cookie in error text
        raise DiscogsHTTPError(e.code, url.split('?', 1)[0], body) from e


def graphql_get(
    auth: dict[str, str],
    *,
    endpoint: str,
    operation_name: str,
    sha256_hash: str,
    variables: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: int = 60,
    retries: int = 3,
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
    return get_json(url, auth, extra, timeout=timeout, retries=retries)
