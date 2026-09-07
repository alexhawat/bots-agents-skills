"""cli_main is the single place SystemExit is raised."""
from __future__ import annotations

import pytest

from _lib.errors import (
    ConfirmationRequired,
    HeadlessRunnerError,
    WhatsAppAuthError,
    WhatsAppError,
    cli_main,
)


def test_hierarchy_allows_catching_everything_with_one_base():
    for exc in (
        WhatsAppAuthError("x"),
        HeadlessRunnerError(1, {}),
        ConfirmationRequired("x"),
    ):
        assert isinstance(exc, WhatsAppError)


def test_headless_runner_error_carries_exit_code_and_payload():
    e = HeadlessRunnerError(3, {"ok": False, "error": "boom"})
    assert e.exit_code == 3
    assert e.payload == {"ok": False, "error": "boom"}
    assert "3" in str(e) and "boom" in str(e)


def test_headless_runner_error_message_omits_full_payload():
    """Page data in the payload must not reach logs via the exception text."""
    e = HeadlessRunnerError(1, {"ok": False, "error": "x", "chats": ["private"]})
    assert "private" not in str(e)


@pytest.mark.parametrize(
    ("fn", "code"),
    [
        (lambda: None, 0),
        (lambda: 0, 0),
        (lambda: 3, 3),
    ],
)
def test_success_exit_codes(fn, code):
    with pytest.raises(SystemExit) as ei:
        cli_main(fn)
    assert ei.value.code == code


def test_confirmation_required_exits_2():
    def fn():
        raise ConfirmationRequired("")

    with pytest.raises(SystemExit) as ei:
        cli_main(fn)
    assert ei.value.code == 2


def test_expected_errors_exit_1_with_message(capsys):
    def fn():
        raise WhatsAppAuthError("session dead")

    with pytest.raises(SystemExit) as ei:
        cli_main(fn)
    assert ei.value.code == 1
    assert "session dead" in capsys.readouterr().err


def test_unexpected_exceptions_are_not_swallowed():
    """A real bug should keep its traceback, not become exit 1."""

    def fn():
        raise ValueError("bug")

    with pytest.raises(ValueError):
        cli_main(fn)


def test_keyboard_interrupt_exits_130():
    def fn():
        raise KeyboardInterrupt

    with pytest.raises(SystemExit) as ei:
        cli_main(fn)
    assert ei.value.code == 130
