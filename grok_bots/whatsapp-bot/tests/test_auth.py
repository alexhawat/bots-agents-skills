"""Auth loading: pointer files, merge order, WA_* overlay, typed failures."""
from __future__ import annotations

import pytest

from _lib import auth
from _lib.errors import WhatsAppAuthError


@pytest.fixture
def pointers(tmp_path, monkeypatch, clean_wa_env):
    """Point the auth loader at tmp_path pointer files (never the real jar)."""
    monkeypatch.setattr(auth, "AUTH_PTR", tmp_path / "AUTH_PATH.txt")
    monkeypatch.setattr(auth, "PERSONAL_PTR", tmp_path / "PERSONAL_PATH.txt")
    return tmp_path


def test_personal_overrides_auth_env(pointers):
    jar = pointers / "auth.env"
    jar.write_text("COOKIE=jar\nUSER_AGENT=ua1\n")
    personal = pointers / "personal.env"
    personal.write_text("USER_AGENT=ua2\n")
    (pointers / "AUTH_PATH.txt").write_text(str(jar))
    (pointers / "PERSONAL_PATH.txt").write_text(str(personal))
    env = auth.load()
    assert env["USER_AGENT"] == "ua2"  # later file wins
    assert env["COOKIE"] == "jar"


def test_wa_prefixed_environment_wins_over_files(pointers, monkeypatch):
    jar = pointers / "auth.env"
    jar.write_text("COOKIE=jar\n")
    (pointers / "AUTH_PATH.txt").write_text(str(jar))
    monkeypatch.setenv("WA_COOKIE", "env-cookie")
    assert auth.load()["WA_COOKIE"] == "env-cookie"
    assert auth.require_cookie() == "jar"  # COOKIE key is checked first


def test_missing_pointers_fall_back_to_box_paths(pointers):
    assert auth.auth_env_path() == auth.DEFAULT_AUTH_ENV
    assert auth.personal_env_path() == auth.DEFAULT_PERSONAL_ENV
    assert auth.load() == {}  # box paths absent in test env


def test_require_cookie_raises_typed_error_not_systemexit(pointers):
    with pytest.raises(WhatsAppAuthError):
        auth.require_cookie()


def test_require_cookie_accepts_wa_cookie(pointers, monkeypatch):
    monkeypatch.setenv("WA_COOKIE", "env-cookie")
    assert auth.require_cookie() == "env-cookie"


def test_no_cookie_value_appears_in_the_error_text(pointers):
    jar = pointers / "auth.env"
    jar.write_text("USER_AGENT=someone\n")
    (pointers / "AUTH_PATH.txt").write_text(str(jar))
    with pytest.raises(WhatsAppAuthError) as ei:
        auth.require_cookie()
    assert "someone" not in str(ei.value)
