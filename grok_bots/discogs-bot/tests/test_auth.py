"""Auth loading: merge order, env overrides, and typed failures."""
from __future__ import annotations

import pytest
from _lib.auth import _parse_env, get_username, load_auth, personal_path, shared_auth_path
from _lib.errors import DiscogsAuthError


def test_parse_env_skips_comments_blanks_and_strips_quotes(tmp_path):
    p = tmp_path / "a.env"
    p.write_text('# comment\n\nCOOKIE="abc=1; def=2"\nUSER_AGENT=\'UA/1.0\'\nNOEQUALS\n')
    assert _parse_env(p) == {"COOKIE": "abc=1; def=2", "USER_AGENT": "UA/1.0"}


def test_parse_env_missing_file_is_empty(tmp_path):
    assert _parse_env(tmp_path / "nope.env") == {}


def test_cookie_value_containing_equals_survives(tmp_path):
    """Cookie jars are full of '='. Splitting on the first one only is load-bearing."""
    p = tmp_path / "a.env"
    p.write_text("COOKIE=sid=xyz==; session=abc=\n")
    assert _parse_env(p)["COOKIE"] == "sid=xyz==; session=abc="


def test_personal_overrides_shared_for_non_secrets(isolated_auth):
    (isolated_auth / "auth.env").write_text("COOKIE=jar\nUSERNAME=from_shared\n")
    (isolated_auth / "personal.env").write_text("USERNAME=from_personal\nCURRENCY=EUR\n")
    auth = load_auth()
    assert auth["USERNAME"] == "from_personal"  # later file wins
    assert auth["CURRENCY"] == "EUR"
    assert auth["COOKIE"] == "jar"


def test_task_local_then_explicit_override_win(isolated_auth, tmp_path):
    (isolated_auth / "auth.env").write_text("COOKIE=jar\nCURRENCY=EUR\n")
    task = tmp_path / "task"
    task.mkdir()
    (task / "auth.env").write_text("CURRENCY=GBP\n")
    override = tmp_path / "override.env"
    override.write_text("CURRENCY=USD\n")

    assert load_auth(task_root=task)["CURRENCY"] == "GBP"
    assert load_auth(task_root=task, override=override)["CURRENCY"] == "USD"


def test_missing_cookie_raises_typed_error_not_systemexit(isolated_auth):
    (isolated_auth / "auth.env").write_text("USERNAME=someone\n")
    with pytest.raises(DiscogsAuthError):
        load_auth()


def test_missing_username_raises_typed_error():
    with pytest.raises(DiscogsAuthError):
        get_username({"COOKIE": "jar"})


def test_env_var_overrides_win_over_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path / "dir"))
    monkeypatch.setenv("DISCOGS_AUTH_ENV", str(tmp_path / "custom-auth.env"))
    monkeypatch.setenv("DISCOGS_PERSONAL_ENV", str(tmp_path / "custom-personal.env"))
    assert shared_auth_path() == tmp_path / "custom-auth.env"
    assert personal_path() == tmp_path / "custom-personal.env"


def test_a_plain_clone_can_point_at_its_own_jar(tmp_path, monkeypatch):
    """The box paths must not be required — this is the regression for hardcoding."""
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path))
    monkeypatch.delenv("DISCOGS_AUTH_ENV", raising=False)
    (tmp_path / "auth.env").write_text("COOKIE=jar\n")
    assert load_auth()["COOKIE"] == "jar"


def test_no_cookie_value_appears_in_the_error_text(isolated_auth):
    (isolated_auth / "auth.env").write_text("USERNAME=someone\n")
    with pytest.raises(DiscogsAuthError) as ei:
        load_auth()
    assert "someone" not in str(ei.value)
