"""envfile.py: shared KEY=VALUE parser, and the cross-pack sync guard."""
from __future__ import annotations

from pathlib import Path

import pytest
from _lib import envfile
from _lib.envfile import merge_env, parse_env

# discogs-scripts/_lib/envfile.py -> parents[3] is grok_bots/
SIBLING = (
    Path(envfile.__file__).resolve().parents[3] / "whatsapp-bot" / "_lib" / "envfile.py"
)


def test_parse_env_skips_comments_blanks_and_strips_quotes(tmp_path):
    p = tmp_path / "a.env"
    p.write_text('# comment\n\nCOOKIE="abc=1; def=2"\nUSER_AGENT=\'UA/1.0\'\nNOEQUALS\n')
    assert parse_env(p) == {"COOKIE": "abc=1; def=2", "USER_AGENT": "UA/1.0"}


def test_parse_env_missing_file_is_empty(tmp_path):
    assert parse_env(tmp_path / "nope.env") == {}


def test_merge_env_later_file_wins(tmp_path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("K=from_a\nONLY_A=1\n")
    b.write_text("K=from_b\n")
    assert merge_env(a, b) == {"K": "from_b", "ONLY_A": "1"}
    assert merge_env(b, a)["K"] == "from_a"


def test_envfile_matches_whatsapp_pack_copy():
    """The packs install separately, so the file is duplicated — this test is
    the drift guard. Skips on a box install where only this pack was copied."""
    if not SIBLING.is_file():
        pytest.skip("sibling whatsapp-bot pack not present (box install)")
    assert Path(envfile.__file__).read_bytes() == SIBLING.read_bytes()
