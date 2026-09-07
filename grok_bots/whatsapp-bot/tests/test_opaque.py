"""opaque.py: the HTTP replay gate, offline against tmp capture dirs."""
from __future__ import annotations

import pytest

from _lib.opaque import (
    endpoints_path,
    has_real_endpoints,
    load_endpoints,
    refuse_http,
    require_http_or_exit,
)


def test_missing_endpoints_file_is_status_none(tmp_path):
    assert load_endpoints(tmp_path) == {"status": "none", "endpoints": []}
    assert not has_real_endpoints(tmp_path)


def test_invalid_json_is_treated_as_no_capture(tmp_path):
    (tmp_path / "capture").mkdir()
    endpoints_path(tmp_path).write_text("not json {")
    assert load_endpoints(tmp_path)["status"] == "none"


def test_status_without_real_urls_is_still_opaque(tmp_path):
    (tmp_path / "capture").mkdir()
    endpoints_path(tmp_path).write_text('{"status": "opaque_ws", "endpoints": [{"note": "x"}]}')
    assert not has_real_endpoints(tmp_path)


def test_endpoint_with_url_counts_as_real(tmp_path):
    (tmp_path / "capture").mkdir()
    endpoints_path(tmp_path).write_text(
        '{"status": "captured", "endpoints": [{"method": "GET", "url": "https://x/"}]}'
    )
    assert has_real_endpoints(tmp_path)
    eps = require_http_or_exit(tmp_path, "slug")
    assert eps[0]["url"] == "https://x/"


def test_refuse_http_exits_2_without_inventing_urls(tmp_path, capsys):
    with pytest.raises(SystemExit) as ei:
        refuse_http(tmp_path, "my-slug")
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "TRAFFIC_OPAQUE" in err and "my-slug" in err


def test_require_http_or_exit_refuses_when_opaque(tmp_path):
    with pytest.raises(SystemExit) as ei:
        require_http_or_exit(tmp_path, "slug")
    assert ei.value.code == 2
