"""Shared test helpers.

`_lib` is importable via pyproject's `pythonpath = ["discogs-scripts"]`. Task
scripts live at `<slug>/scripts/<name>.py` and are not packages, so they are
loaded by path.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PACK_ROOT / "discogs-scripts"

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


def load_script(slug: str, module: str):
    """Import a task script by path, e.g. load_script('orders-list', 'orders')."""
    path = SCRIPTS_ROOT / slug / "scripts" / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"_script_{slug}_{module}", path)
    assert spec and spec.loader, path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def scripts_root() -> Path:
    return SCRIPTS_ROOT


@pytest.fixture(scope="session")
def marketplace_row_html() -> str:
    return (SCRIPTS_ROOT / "marketplace-search" / "capture" / "sample-row.html").read_text()


@pytest.fixture(scope="session")
def collection_har() -> Path:
    return SCRIPTS_ROOT / "collection-search" / "capture" / "collection-federico.har"


@pytest.fixture
def isolated_auth(tmp_path, monkeypatch):
    """Point the auth loader at a temp dir so tests never touch a real jar."""
    monkeypatch.setenv("DISCOGS_AUTH_DIR", str(tmp_path))
    monkeypatch.delenv("DISCOGS_AUTH_ENV", raising=False)
    monkeypatch.delenv("DISCOGS_PERSONAL_ENV", raising=False)
    return tmp_path


def load_auth_helper(module: str):
    """Import a discogs-auth helper by path (they are scripts, not a package)."""
    path = PACK_ROOT / "discogs-auth" / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"_authhelper_{module}", path)
    assert spec and spec.loader, path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
