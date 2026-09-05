"""POST Discogs catalog GraphQL persisted mutations. Never log Cookie / secrets."""
from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.request
from typing import Any

from _lib.errors import ConfirmationRequired, DiscogsHTTPError
from _lib.http import DEFAULT_UA

GRAPHQL_URL = "https://www.discogs.com/service/catalog/api/graphql"


def graphql_mutate(
    auth: dict[str, str],
    *,
    operation_name: str,
    sha256_hash: str,
    variables: dict[str, Any],
    endpoint: str = GRAPHQL_URL,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> Any:
    """POST a persisted GraphQL mutation.

    Body: {operationName, variables, extensions:{persistedQuery:{version:1,sha256Hash}}}
    Headers: cookie, user-agent, apollographql-client-name, accept application/json,
    content-type application/json, referer https://www.discogs.com/
    """
    body = {
        "operationName": operation_name,
        "variables": variables,
        "extensions": {
            "persistedQuery": {"version": 1, "sha256Hash": sha256_hash},
        },
    }
    payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
    req_headers: dict[str, str] = {
        "accept": "application/json",
        "accept-encoding": "identity",
        "content-type": "application/json",
        "user-agent": auth.get("USER_AGENT", DEFAULT_UA),
        "cookie": auth["COOKIE"],
        "referer": "https://www.discogs.com/",
        "origin": "https://www.discogs.com",
        "apollographql-client-name": auth.get(
            "APOLLO_CLIENT_NAME", "release-page-client"
        ),
    }
    if auth.get("AUTHORIZATION"):
        req_headers["authorization"] = auth["AUTHORIZATION"]
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(
        endpoint, data=payload, headers=req_headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            text = data.decode("utf-8", errors="replace")
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        err_body = e.read()[:800]
        # Never include request Cookie in error text
        raise DiscogsHTTPError(e.code, f"GraphQL {operation_name}", err_body) from e


def require_confirm(confirm: bool, planned: str) -> None:
    """If not confirm, print the planned mutation and abort with exit code 2."""
    if confirm:
        return
    print(planned)
    print("# dry-run: pass --confirm to execute (exit 2)")
    raise ConfirmationRequired("")
