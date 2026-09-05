"""Load Discogs session auth: shared jar + personal overrides + task-local.

Paths default to the Grok Bot box layout but every one is environment
overridable, so a plain clone can point at its own jar:

    export DISCOGS_AUTH_DIR=~/.config/discogs-bot
    export DISCOGS_AUTH_ENV=/custom/auth.env      # wins over DISCOGS_AUTH_DIR
    export DISCOGS_PERSONAL_ENV=/custom/personal.env
"""
from __future__ import annotations

import os
from pathlib import Path

from _lib.errors import DiscogsAuthError

DEFAULT_AUTH_DIR = Path("/home/box/discogs-auth")


def auth_dir() -> Path:
    """Directory holding auth.env / personal.env."""
    return Path(os.environ.get("DISCOGS_AUTH_DIR") or DEFAULT_AUTH_DIR)


def shared_auth_path() -> Path:
    """Canonical Cookie jar."""
    override = os.environ.get("DISCOGS_AUTH_ENV")
    return Path(override) if override else auth_dir() / "auth.env"


def personal_path() -> Path:
    """Non-secret personal overrides (USERNAME, CURRENCY, ...)."""
    override = os.environ.get("DISCOGS_PERSONAL_ENV")
    return Path(override) if override else auth_dir() / "personal.env"


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_auth(task_root: Path | None = None, override: Path | None = None) -> dict[str, str]:
    """Merge env files. Order: shared auth -> personal -> task_root/auth.env -> override."""
    ordered: list[Path] = [shared_auth_path(), personal_path()]
    if task_root is not None:
        ordered.append(Path(task_root) / "auth.env")
    if override is not None:
        ordered.append(Path(override))

    merged: dict[str, str] = {}
    for path in ordered:
        merged.update(_parse_env(path))

    if not merged.get("COOKIE"):
        raise DiscogsAuthError(
            f"COOKIE missing (looked in {shared_auth_path()}). Sign in via Discogs-Bot "
            "Chrome, then run `python3 discogs-auth/export_cookies.py`, or set "
            "DISCOGS_AUTH_ENV to a jar containing COOKIE=..."
        )
    return merged


def get_username(auth: dict[str, str] | None = None) -> str:
    data = auth if auth is not None else load_auth()
    user = (data.get("USERNAME") or "").strip()
    if not user:
        raise DiscogsAuthError(
            f"USERNAME missing. Set it in {personal_path()} "
            "(never put it in the bot persona)."
        )
    return user
