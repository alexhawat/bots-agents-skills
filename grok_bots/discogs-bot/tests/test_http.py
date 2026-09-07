"""http.py: bounded retry on 429/5xx, Retry-After honored, URL stripping."""
from __future__ import annotations

import io
import urllib.error

import pytest
from _lib import http
from _lib.errors import DiscogsHTTPError

AUTH = {"COOKIE": "jar"}


class _Resp:
    """Minimal urlopen context-manager response."""

    def __init__(self, data: bytes = b"{}"):
        self._data = data
        self.headers: dict[str, str] = {}

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://x", code, "err", headers, io.BytesIO(b"boom"))


class _Flaky:
    """Fake urlopen: fail `code` `failures` times (Retry-After optional), then 200."""

    def __init__(self, code: int, failures: int = 99, retry_after: str | None = None):
        self.code = code
        self.left = failures
        self.retry_after = retry_after
        self.calls = 0

    def __call__(self, req, timeout=0):
        self.calls += 1
        if self.left > 0:
            self.left -= 1
            raise _http_error(self.code, self.retry_after)
        return _Resp(b'{"ok": true}')


@pytest.fixture
def sleeps(monkeypatch):
    out: list[float] = []
    monkeypatch.setattr(http.time, "sleep", out.append)
    return out


def test_429_then_200_retries_and_honors_retry_after(monkeypatch, sleeps):
    fake = _Flaky(429, failures=1, retry_after="7")
    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    assert http.get_json("https://api.discogs.com/x", AUTH) == {"ok": True}
    assert fake.calls == 2
    assert sleeps == [7.0]


def test_retry_after_is_capped(monkeypatch, sleeps):
    monkeypatch.setattr(http.urllib.request, "urlopen", _Flaky(429, retry_after="120"))
    with pytest.raises(DiscogsHTTPError):
        http.get_bytes("https://api.discogs.com/x", AUTH)
    assert sleeps[0] == http.MAX_RETRY_WAIT
    assert all(s <= http.MAX_RETRY_WAIT for s in sleeps)


def test_5xx_retries_then_raises_with_status(monkeypatch, sleeps):
    fake = _Flaky(503)
    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    with pytest.raises(DiscogsHTTPError) as ei:
        http.get_bytes("https://api.discogs.com/x", AUTH)
    assert ei.value.status == 503
    assert fake.calls == 3  # default: 3 attempts
    assert len(sleeps) == 2


def test_backoff_grows_without_retry_after(monkeypatch, sleeps):
    monkeypatch.setattr(http.urllib.request, "urlopen", _Flaky(500))
    with pytest.raises(DiscogsHTTPError):
        http.get_bytes("https://api.discogs.com/x", AUTH)
    assert len(sleeps) == 2
    assert sleeps[0] < sleeps[1]  # exponential backoff (jitter is sub-second)


def test_4xx_other_than_429_is_never_retried(monkeypatch, sleeps):
    fake = _Flaky(404)
    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    with pytest.raises(DiscogsHTTPError) as ei:
        http.get_bytes("https://api.discogs.com/x", AUTH)
    assert ei.value.status == 404
    assert fake.calls == 1
    assert sleeps == []


def test_retries_kwarg_controls_attempts(monkeypatch, sleeps):
    fake = _Flaky(500)
    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    with pytest.raises(DiscogsHTTPError):
        http.get_bytes("https://api.discogs.com/x", AUTH, retries=1)
    assert fake.calls == 1
    assert sleeps == []


def test_error_url_strips_query_string(monkeypatch, sleeps):
    monkeypatch.setattr(http.urllib.request, "urlopen", _Flaky(401))
    with pytest.raises(DiscogsHTTPError) as ei:
        http.get_bytes("https://www.discogs.com/x?token=secret", AUTH)
    assert ei.value.url == "https://www.discogs.com/x"


def test_get_public_json_strips_query_string(monkeypatch):
    """Regression: get_public_json used to leak the query into the error URL."""
    monkeypatch.setattr(http.urllib.request, "urlopen", _Flaky(404))
    with pytest.raises(DiscogsHTTPError) as ei:
        http.get_public_json("https://api.discogs.com/releases/1?key=secret")
    assert ei.value.url == "https://api.discogs.com/releases/1"


def test_error_text_never_carries_cookie(monkeypatch, sleeps):
    monkeypatch.setattr(http.urllib.request, "urlopen", _Flaky(401))
    with pytest.raises(DiscogsHTTPError) as ei:
        http.get_bytes("https://www.discogs.com/x", {"COOKIE": "sid=supersecret"})
    assert "supersecret" not in str(ei.value)
