"""The committed-HAR guard.

HAR keeps credentials in four places; a guard that checks only request headers
passes a file whose parsed `cookies[]` array is full of live values.
"""
from __future__ import annotations

import json

import pytest


@pytest.fixture(scope="module")
def guard():
    import importlib.util

    from conftest import PACK_ROOT
    path = PACK_ROOT / "tools" / "har_guard.py"
    spec = importlib.util.spec_from_file_location("_har_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _har(request=None, response=None) -> dict:
    return {"log": {"entries": [{
        "request": request or {"headers": [], "cookies": []},
        "response": response or {"headers": [], "cookies": []},
    }]}}


def _write(tmp_path, name, payload):
    p = tmp_path / name
    p.write_text(json.dumps(payload))
    return p


def test_shipped_fixtures_are_clean(guard, scripts_root):
    for har in sorted(scripts_root.rglob("*.har")):
        assert guard.scan_har(har) == [], f"{har} carries live session material"


def test_redacted_placeholders_pass(guard, tmp_path):
    for value in ("REDACTED", "PLACEHOLDER", "", "<redacted>", "redacted"):
        p = _write(tmp_path, "c.har",
                   _har(request={"headers": [{"name": "Cookie", "value": value}],
                                 "cookies": []}))
        assert guard.scan_har(p) == [], f"{value!r} should count as redacted"


def test_live_request_cookie_header_is_caught(guard, tmp_path):
    p = _write(tmp_path, "c.har",
               _har(request={"headers": [{"name": "Cookie", "value": "session=live"}],
                             "cookies": []}))
    assert guard.scan_har(p)


def test_live_cookies_array_is_caught_even_when_headers_are_clean(guard, tmp_path):
    """Regression: the first guard checked request headers only and passed this."""
    p = _write(tmp_path, "c.har",
               _har(request={"headers": [{"name": "Cookie", "value": "REDACTED"}],
                             "cookies": [{"name": "session", "value": "LIVE_VALUE"}]}))
    findings = guard.scan_har(p)
    assert findings
    assert "request.cookies[session]" in findings[0]


def test_response_set_cookie_is_caught(guard, tmp_path):
    p = _write(tmp_path, "c.har",
               _har(response={"headers": [{"name": "Set-Cookie", "value": "sid=live; Path=/"}],
                              "cookies": []}))
    assert guard.scan_har(p)


def test_response_cookies_array_is_caught(guard, tmp_path):
    p = _write(tmp_path, "c.har",
               _har(response={"headers": [], "cookies": [{"name": "sid", "value": "live"}]}))
    assert guard.scan_har(p)


def test_authorization_header_is_caught(guard, tmp_path):
    p = _write(tmp_path, "c.har",
               _har(request={"headers": [{"name": "Authorization", "value": "Bearer real.jwt"}],
                             "cookies": []}))
    assert guard.scan_har(p)


def test_header_matching_is_case_insensitive(guard, tmp_path):
    p = _write(tmp_path, "c.har",
               _har(request={"headers": [{"name": "COOKIE", "value": "session=live"}],
                             "cookies": []}))
    assert guard.scan_har(p)


def test_unreadable_har_is_treated_as_suspect_not_clean(guard, tmp_path):
    """Failing open on a malformed file would defeat the guard."""
    p = tmp_path / "broken.har"
    p.write_text("{not json")
    assert guard.scan_har(p)


def test_findings_never_echo_the_secret_value(guard, tmp_path):
    """CI logs are public on many repos; the guard must not print what it found."""
    p = _write(tmp_path, "c.har",
               _har(request={"headers": [{"name": "Cookie", "value": "SUPERSECRETVALUE"}],
                             "cookies": [{"name": "sid", "value": "ANOTHERSECRET"}]}))
    blob = " ".join(guard.scan_har(p))
    assert "SUPERSECRETVALUE" not in blob
    assert "ANOTHERSECRET" not in blob


def test_cli_exit_codes(guard, tmp_path, capsys):
    clean = _write(tmp_path, "clean.har",
                   _har(request={"headers": [{"name": "Cookie", "value": "REDACTED"}],
                                 "cookies": []}))
    dirty = _write(tmp_path, "dirty.har",
                   _har(request={"headers": [], "cookies": [{"name": "s", "value": "live"}]}))
    assert guard.main(["har_guard.py", str(clean)]) == 0
    assert guard.main(["har_guard.py", str(dirty)]) == 1
    assert guard.main(["har_guard.py", str(clean), str(dirty)]) == 1
    assert guard.main(["har_guard.py"]) == 2  # no args


def test_cli_emits_a_github_annotation(guard, tmp_path, capsys):
    dirty = _write(tmp_path, "dirty.har",
                   _har(request={"headers": [{"name": "Cookie", "value": "live"}], "cookies": []}))
    guard.main(["har_guard.py", str(dirty)])
    assert "::error file=" in capsys.readouterr().out
