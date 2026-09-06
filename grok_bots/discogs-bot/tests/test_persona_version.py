"""The persona `// version` marker and its copy in the skill doc must agree.

The standing gate is that a material capability or auth change bumps the minor.
That is a convention a reviewer has to remember — it was missed once already —
so the mechanical half (the two markers not drifting apart) is checked here.
"""
from __future__ import annotations

import re

import pytest
from conftest import PACK_ROOT

PERSONA = PACK_ROOT / "PERSONA.md"
SKILL = PACK_ROOT / "docs" / "discogs-capture-to-script.SKILL.md"

VERSION_RE = re.compile(r"^//\s*version\s*\n\s*(\d+)\.(\d+)", re.M)


def persona_version() -> tuple[int, int]:
    m = VERSION_RE.search(PERSONA.read_text())
    assert m, "PERSONA.md charter is missing a `// version` marker"
    return int(m.group(1)), int(m.group(2))


def test_persona_declares_a_version():
    major, minor = persona_version()
    assert major >= 4, "version went backwards"


def test_skill_doc_markers_match_the_persona():
    major, minor = persona_version()
    text = SKILL.read_text()
    expected = f"{major}.{minor}"
    found = set(re.findall(r"(?:// version |persona v)(\d+\.\d+)", text))
    assert found, "skill doc records no persona version"
    assert found == {expected}, (
        f"skill doc records {sorted(found)} but PERSONA.md says {expected} — "
        "bump both together"
    )


@pytest.mark.parametrize("marker", ["// one job", "// auth (self-owned)", "// anti-jobs"])
def test_charter_sections_survive_edits(marker):
    """Cheap guard: a botched sed on the charter should fail loudly here."""
    assert marker in PERSONA.read_text()


def test_persona_still_carries_no_owner_identity():
    """The charter forbids names/usernames/locations in itself — enforce it."""
    text = PERSONA.read_text().lower()
    for leaked in ("alex", "@gmail", "eggbot"):
        assert leaked not in text, f"{leaked!r} must not appear in the persona"
