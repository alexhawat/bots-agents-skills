"""Shared test helpers.

`_lib` is importable via pyproject's `pythonpath = ["."]`. Task scripts live at
`<slug>/scripts/<name>.py` and are not packages, so they are loaded by path.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[1]


def load_script(slug: str, module: str):
    """Import a task script by path, e.g. load_script('har-diff', 'diff')."""
    path = PACK_ROOT / slug / "scripts" / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"_script_{slug}_{module}", path)
    assert spec and spec.loader, path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def clean_wa_env(monkeypatch):
    """Drop every WA_* variable so tests never see a developer's real session."""
    for key in list(os.environ):
        if key.startswith("WA_"):
            monkeypatch.delenv(key, raising=False)
