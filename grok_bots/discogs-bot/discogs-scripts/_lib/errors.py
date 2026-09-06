"""Typed errors for the Discogs pack.

The library layer raises these instead of ``SystemExit`` so that callers can
branch on failure *kind* (see auth-refresh, which needs to tell a dead session
from a network blip) and so the parsers stay importable under test.

Scripts turn them into exit codes exactly once, in ``cli_main``.
"""
from __future__ import annotations

import sys
from typing import Callable, NoReturn


class DiscogsError(Exception):
    """Base for every expected failure in this pack."""


class DiscogsAuthError(DiscogsError):
    """Missing/!dead session material: no COOKIE, no USERNAME, viewer=null."""


class DiscogsHTTPError(DiscogsError):
    """Non-2xx from Discogs. Carries the status so callers need not parse text.

    ``body`` is truncated by the caller and never contains request headers —
    the Cookie must not reach logs or tracebacks.
    """

    def __init__(self, status: int, url: str, body: bytes | str = b"") -> None:
        self.status = status
        self.url = url
        self.body = body
        super().__init__(f"HTTP {status} for {url}: {body!r}")


class DiscogsAPIError(DiscogsError):
    """Transport succeeded but the payload carried GraphQL ``errors``."""


class ConfirmationRequired(DiscogsError):
    """A mutation was requested without its confirm flag(s). Exits 2, not 1."""


def cli_main(fn: Callable[[], int | None]) -> NoReturn:
    """Run a script ``main`` and map expected errors to exit codes.

    0/None success · 2 confirmation withheld · 1 anything we anticipated.
    Unexpected exceptions keep their traceback — those are bugs, not user error.
    """
    try:
        rc = fn()
    except ConfirmationRequired as e:
        if str(e):
            print(str(e), file=sys.stderr)
        raise SystemExit(2) from e
    except DiscogsError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    raise SystemExit(rc or 0)
