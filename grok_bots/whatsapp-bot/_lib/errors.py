"""Typed errors for the WhatsApp pack.

The library layer raises these instead of ``SystemExit`` so that callers can
branch on failure *kind* and so the helpers stay importable under test.

Scripts turn them into exit codes exactly once, in ``cli_main``.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, NoReturn


class WhatsAppError(Exception):
    """Base for every expected failure in this pack."""


class WhatsAppAuthError(WhatsAppError):
    """Missing session material: no COOKIE / WA_COOKIE in the merged env."""


class HeadlessRunnerError(WhatsAppError):
    """The node headless runner exited nonzero.

    Carries the runner's exit code and its parsed JSON payload. The message
    carries only the payload's ``error`` field — never the full payload, which
    may hold page data.
    """

    def __init__(self, exit_code: int, payload: dict[str, Any]) -> None:
        self.exit_code = exit_code
        self.payload = payload
        detail = payload.get("error") or "unknown runner failure"
        super().__init__(f"headless runner exited {exit_code}: {detail}")


class ConfirmationRequired(WhatsAppError):
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
    except WhatsAppError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    raise SystemExit(rc or 0)
