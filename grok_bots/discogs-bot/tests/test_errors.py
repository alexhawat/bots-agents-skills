"""cli_main is the single place SystemExit is raised."""
from __future__ import annotations

import pytest
from _lib.errors import (
    ConfirmationRequired,
    DiscogsAPIError,
    DiscogsAuthError,
    DiscogsError,
    DiscogsHTTPError,
    cli_main,
)


def test_hierarchy_allows_catching_everything_with_one_base():
    for exc in (
        DiscogsAuthError("x"),
        DiscogsAPIError("x"),
        DiscogsHTTPError(500, "u"),
        ConfirmationRequired("x"),
    ):
        assert isinstance(exc, DiscogsError)


def test_http_error_exposes_status_so_callers_need_no_string_matching():
    """The regression for refresh.py's old `if "HTTP 401" in str(e)`."""
    e = DiscogsHTTPError(401, "https://www.discogs.com/x", b"denied")
    assert e.status == 401
    assert e.url == "https://www.discogs.com/x"


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
        raise DiscogsAuthError("session dead")

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
