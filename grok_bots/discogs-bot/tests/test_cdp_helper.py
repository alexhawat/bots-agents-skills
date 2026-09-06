"""The CDP exporter, exercised through node.

Importing this module must not open a CDP session or write the jar: the file
is both a CLI and a source of path helpers, and an import-time side effect
there would mean merely reading a path could overwrite a live cookie jar.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess

import pytest
from conftest import PACK_ROOT

HELPER = PACK_ROOT / "discogs-auth" / "export_from_display.mjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _node(script: str, env: dict[str, str] | None = None, cwd=None):
    full = dict(os.environ)
    full.pop("DISCOGS_AUTH_ENV", None)
    full.update(env or {})
    return subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, env=full, cwd=cwd,
    )


def test_module_parses(tmp_path):
    r = subprocess.run(["node", "--check", str(HELPER)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_importing_the_module_has_no_side_effects(tmp_path):
    """Regression: the CDP body used to run at import via top-level await.

    The sand-host modules do not exist off-box, so an eager static import also
    made the file unimportable anywhere but the box.
    """
    jar, work = tmp_path / "jar", tmp_path / "work"
    r = _node(
        f'const m = await import({json.dumps(str(HELPER))});'
        'console.log(JSON.stringify({out: m.outPath(), work: m.workDir()}));',
        {"DISCOGS_AUTH_DIR": str(jar), "DISCOGS_WORK_AUTH": str(work)},
    )
    assert r.returncode == 0, r.stderr
    paths = json.loads(r.stdout.strip().splitlines()[-1])
    assert paths["out"] == str(jar / "auth.env")
    assert paths["work"] == str(work)
    # Nothing may have been created merely by importing.
    assert not jar.exists()
    assert not work.exists()


def test_path_helpers_resolve_per_call(tmp_path):
    r = _node(
        f'const m = await import({json.dumps(str(HELPER))});'
        'const a = m.outPath();'
        'process.env.DISCOGS_AUTH_ENV = "/tmp/changed.env";'
        'console.log(JSON.stringify([a, m.outPath()]));',
        {"DISCOGS_AUTH_DIR": str(tmp_path)},
    )
    assert r.returncode == 0, r.stderr
    first, second = json.loads(r.stdout.strip().splitlines()[-1])
    assert first == str(tmp_path / "auth.env")
    assert second == "/tmp/changed.env"


def test_write_jar_creates_0600_jar_and_pointer_only(tmp_path):
    jar, work = tmp_path / "jar", tmp_path / "work"
    r = _node(
        f'const m = await import({json.dumps(str(HELPER))});'
        'const j = new Map([["session", {name:"session", value:"v1", domain:"www.discogs.com"}]]);'
        'console.log(JSON.stringify(m.writeJar(m.pickCookies(j))));',
        {"DISCOGS_AUTH_DIR": str(jar), "DISCOGS_WORK_AUTH": str(work)},
    )
    assert r.returncode == 0, r.stderr
    out = jar / "auth.env"
    assert stat.S_IMODE(os.stat(out).st_mode) == 0o600
    assert "COOKIE=session=v1" in out.read_text()
    # The work tree gets a pointer and nothing else — never a copy of the jar.
    assert sorted(p.name for p in work.iterdir()) == ["AUTH_PATH.txt"]
    assert (work / "AUTH_PATH.txt").read_text().strip() == str(out)


def test_cookie_picking_prefers_www_over_login_domain(tmp_path):
    r = _node(
        f'const m = await import({json.dumps(str(HELPER))});'
        'const j = new Map(['
        '  ["a", {name:"session", value:"login", domain:"login.discogs.com"}],'
        '  ["b", {name:"session", value:"www", domain:"www.discogs.com"}]]);'
        'const picked = m.pickCookies(j);'
        'console.log(picked.get("session").value);',
        {"DISCOGS_AUTH_DIR": str(tmp_path)},
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "www"


def test_non_discogs_and_valueless_cookies_are_dropped(tmp_path):
    r = _node(
        f'const m = await import({json.dumps(str(HELPER))});'
        'const j = new Map(['
        '  ["a", {name:"other", value:"x", domain:"example.com"}],'
        '  ["b", {name:"empty", value:"", domain:"www.discogs.com"}],'
        '  ["c", {name:"keep", value:"y", domain:"www.discogs.com"}]]);'
        'console.log(JSON.stringify([...m.pickCookies(j).keys()]));',
        {"DISCOGS_AUTH_DIR": str(tmp_path)},
    )
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout.strip().splitlines()[-1]) == ["keep"]


def test_running_as_a_program_off_box_fails_without_touching_the_jar(tmp_path):
    """The main guard runs; the box-only CDP import is what fails, not a syntax error."""
    jar = tmp_path / "jar"
    r = subprocess.run(
        ["node", str(HELPER)],
        capture_output=True, text=True,
        env={**os.environ, "DISCOGS_AUTH_DIR": str(jar), "DISPLAY": ":0"},
    )
    assert r.returncode != 0
    assert not jar.exists(), "a failed run must not leave a partial jar"
