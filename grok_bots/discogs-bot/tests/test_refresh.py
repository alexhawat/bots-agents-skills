"""auth-refresh must tell hash rotation apart from a dead session."""
from __future__ import annotations

import pytest
from _lib.errors import DiscogsHTTPError, PersistedQueryRotated
from conftest import load_script


@pytest.fixture
def refresh():
    return load_script("auth-refresh", "refresh")


def test_check_viewer_rotated_raises_not_http401(refresh, monkeypatch):
    def boom(*a, **k):
        raise PersistedQueryRotated(
            "ViewerCollectionListData",
            status=403,
            body=b"Unsupported query ID",
        )

    monkeypatch.setattr(refresh, "graphql_get", boom)
    with pytest.raises(PersistedQueryRotated):
        refresh.check_viewer({"COOKIE": "x"})


def test_check_viewer_plain_403_is_http401_status(refresh, monkeypatch):
    def boom(*a, **k):
        raise DiscogsHTTPError(403, "https://www.discogs.com/graphql", b"Forbidden")

    monkeypatch.setattr(refresh, "graphql_get", boom)
    status, identity = refresh.check_viewer({"COOKIE": "x"})
    assert status == "http401"
    assert identity is None


def test_main_rotated_exits_without_export(refresh, monkeypatch, capsys, isolated_auth):
    calls = {"export": 0}

    def fake_export():
        calls["export"] += 1
        return 0

    monkeypatch.setattr(refresh, "run_export", fake_export)
    monkeypatch.setattr(
        refresh,
        "load_auth",
        lambda **k: {"COOKIE": "x", "USER_AGENT": "UA"},
    )
    monkeypatch.setattr(
        refresh,
        "check_viewer",
        lambda auth: (_ for _ in ()).throw(
            PersistedQueryRotated("ViewerCollectionListData", status=403)
        ),
    )
    monkeypatch.setattr("sys.argv", ["refresh.py"])
    assert refresh.main() == 1
    err = capsys.readouterr().err
    assert "hash rotated op=ViewerCollectionListData (not a session problem)" in err
    assert calls["export"] == 0
    assert "session dead" not in err
    assert "Semi-manual" not in capsys.readouterr().out


def test_main_plain_403_check_only_is_session_dead(refresh, monkeypatch, capsys, isolated_auth):
    monkeypatch.setattr(
        refresh,
        "load_auth",
        lambda **k: {"COOKIE": "x", "USER_AGENT": "UA"},
    )
    monkeypatch.setattr(refresh, "check_viewer", lambda auth: ("http401", None))
    monkeypatch.setattr("sys.argv", ["refresh.py", "--check-only"])
    assert refresh.main() == 1
    out = capsys.readouterr().out
    assert "dead viewer status=http401" in out
    assert "Semi-manual" in out
