"""The exporters and the loader must never disagree about where the jar lives.

Paths are resolved per call, not at import: a caller that sets DISCOGS_* after
importing the module still gets the path it asked for.
"""
from __future__ import annotations

import json
import os
import stat

import pytest
from _lib.auth import shared_auth_path


@pytest.fixture(scope="module")
def export_cookies():
    from conftest import load_auth_helper
    return load_auth_helper("export_cookies")


@pytest.fixture(scope="module")
def har_to_auth():
    from conftest import load_auth_helper
    return load_auth_helper("har_to_auth")


def test_exporter_and_loader_agree_on_the_jar_path(export_cookies, tmp_path, monkeypatch):
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path))
    monkeypatch.delenv("DISCOGS_AUTH_ENV", raising=False)
    assert export_cookies.out_path() == shared_auth_path()


def test_auth_env_beats_auth_dir(export_cookies, tmp_path, monkeypatch):
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path / "dir"))
    monkeypatch.setenv("DISCOGS_AUTH_ENV", str(tmp_path / "explicit.env"))
    assert export_cookies.out_path() == tmp_path / "explicit.env"
    assert export_cookies.out_path() == shared_auth_path()


def test_paths_are_resolved_per_call_not_at_import(export_cookies, tmp_path, monkeypatch):
    """Regression: OUT/SEED/WORK were module globals fixed at import time."""
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path / "first"))
    first = export_cookies.out_path()
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path / "second"))
    assert export_cookies.out_path() != first
    assert export_cookies.out_path() == tmp_path / "second" / "auth.env"


def test_seed_and_work_dir_are_overridable(export_cookies, tmp_path, monkeypatch):
    monkeypatch.setenv("DISCOGS_COOKIE_SEED", str(tmp_path / "seed.json"))
    monkeypatch.setenv("DISCOGS_WORK_AUTH", str(tmp_path / "work"))
    assert export_cookies.seed_path() == tmp_path / "seed.json"
    assert export_cookies.work_dir() == tmp_path / "work"


def test_box_defaults_apply_with_no_env(export_cookies, monkeypatch):
    for var in ("DISCOGS_AUTH_ENV", "DISCOGS_AUTH_DIR", "DISCOGS_COOKIE_SEED",
                "DISCOGS_WORK_AUTH"):
        monkeypatch.delenv(var, raising=False)
    assert str(export_cookies.out_path()) == "/home/box/discogs-auth/auth.env"
    assert str(export_cookies.work_dir()) == "/workspace/discogs-scripts/_auth"


def test_write_secret_creates_at_0600(export_cookies, tmp_path):
    """Regression: write_text() created at umask default, then chmod'd."""
    target = tmp_path / "nested" / "auth.env"
    export_cookies.write_secret(target, "COOKIE=x\n")
    assert stat.S_IMODE(os.stat(target).st_mode) == 0o600
    assert target.read_text() == "COOKIE=x\n"


def test_write_secret_tightens_an_existing_loose_file(export_cookies, tmp_path):
    target = tmp_path / "auth.env"
    target.write_text("old")
    os.chmod(target, 0o644)
    export_cookies.write_secret(target, "COOKIE=y\n")
    assert stat.S_IMODE(os.stat(target).st_mode) == 0o600


def _har(cookie: str) -> dict:
    return {"log": {"entries": [{"request": {"headers": [
        {"name": "Cookie", "value": cookie},
        {"name": "User-Agent", "value": "UA/1.0"},
    ]}}]}}


def test_har_to_auth_writes_the_jar_at_0600(har_to_auth, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DISCOGS_AUTH_ENV", str(tmp_path / "deep" / "auth.env"))
    har = tmp_path / "c.har"
    har.write_text(json.dumps(_har("session=abcdefghijkl; sid=mnopqrstuvwx")))
    monkeypatch.setattr("sys.argv", ["har_to_auth.py", str(har)])
    assert har_to_auth.main() == 0
    out = tmp_path / "deep" / "auth.env"
    assert stat.S_IMODE(os.stat(out).st_mode) == 0o600
    assert "session=abcdefghijkl" in out.read_text()


def test_har_to_auth_never_prints_the_cookie_value(har_to_auth, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DISCOGS_AUTH_ENV", str(tmp_path / "auth.env"))
    har = tmp_path / "c.har"
    har.write_text(json.dumps(_har("session=SUPERSECRETVALUE")))
    monkeypatch.setattr("sys.argv", ["har_to_auth.py", str(har)])
    har_to_auth.main()
    assert "SUPERSECRETVALUE" not in capsys.readouterr().out


def test_har_to_auth_reports_missing_and_malformed_files(har_to_auth, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["har_to_auth.py", str(tmp_path / "nope.har")])
    assert har_to_auth.main() == 1
    bad = tmp_path / "bad.har"
    bad.write_text("{not json")
    monkeypatch.setattr("sys.argv", ["har_to_auth.py", str(bad)])
    assert har_to_auth.main() == 1


def test_har_to_auth_skips_redacted_cookie_headers(har_to_auth, tmp_path, monkeypatch):
    """A scrubbed HAR must not be mistaken for a usable jar."""
    monkeypatch.setenv("DISCOGS_AUTH_ENV", str(tmp_path / "auth.env"))
    har = tmp_path / "c.har"
    har.write_text(json.dumps(_har("REDACTED")))
    monkeypatch.setattr("sys.argv", ["har_to_auth.py", str(har)])
    assert har_to_auth.main() == 1


def test_cdp_helper_never_copies_the_jar_into_the_checkout():
    """Regression for the PR review blocker.

    The CDP path is *preferred* over the Python seed path, so a copyFileSync
    here silently reintroduced a duplicate secret inside the repo checkout even
    though the Python exporter was clean.
    """
    from conftest import PACK_ROOT
    src = (PACK_ROOT / "discogs-auth" / "export_from_display.mjs").read_text()
    assert "copyFileSync" not in src, "CDP helper must not copy the jar anywhere"
    assert "AUTH_PATH.txt" in src, "CDP helper should still write the path pointer"


def test_cdp_helper_honours_the_same_env_vars_as_python():
    from conftest import PACK_ROOT
    src = (PACK_ROOT / "discogs-auth" / "export_from_display.mjs").read_text()
    for var in ("DISCOGS_AUTH_ENV", "DISCOGS_AUTH_DIR", "DISCOGS_WORK_AUTH"):
        assert var in src, f"CDP helper ignores {var}"


def test_cdp_helper_declares_no_module_level_path_constants():
    """Regression: `const OUT = outPath()` snapshotted the env at process start.

    Behaviour is covered for real in test_cdp_helper.py (via node); this is the
    cheap source-level guard that survives when node is unavailable.
    """
    from conftest import PACK_ROOT
    src = (PACK_ROOT / "discogs-auth" / "export_from_display.mjs").read_text()
    assert "const OUT = outPath()" not in src
    assert "const WORK_DIR = process.env" not in src
    assert "export function outPath()" in src
    assert "export function workDir()" in src


def test_cdp_helper_gates_its_cdp_body_behind_a_main_check():
    """Regression: top-level `await connectBrowser(port)` ran CDP on import.

    Importing the module to read a path must not open a browser session or
    write the jar. Proven behaviourally in test_cdp_helper.py.
    """
    from conftest import PACK_ROOT
    src = (PACK_ROOT / "discogs-auth" / "export_from_display.mjs").read_text()
    assert "import.meta.url === pathToFileURL(process.argv[1]).href" in src
    # the box-only modules must be imported lazily, inside main()
    assert 'import { connectBrowser' not in src
    assert 'await import(' in src


def test_shipped_response_sample_is_synthetic():
    """The pack is public: no real collection inventory in committed fixtures."""
    from conftest import SCRIPTS_ROOT
    sample = json.loads(
        (SCRIPTS_ROOT / "collection-search" / "capture" / "response-sample.json").read_text()
    )
    assert "SYNTHETIC" in sample.get("_note", "").upper()
    for item in sample.get("sample_items", []):
        # Real collection item ids are ~10 digits and unpredictable; the
        # synthetic ones are a fixed, obviously-fake block.
        assert 1000000000 <= item["discogsId"] <= 1000000099
