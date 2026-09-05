"""Load Discogs session auth: shared jar + personal overrides + task-local."""
from __future__ import annotations

from pathlib import Path

SHARED = Path("/home/box/discogs-auth/auth.env")
PERSONAL = Path("/home/box/discogs-auth/personal.env")


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
    """Merge env files. Order: shared auth → personal → task_root/auth.env → override (later wins)."""
    ordered: list[Path] = [SHARED, PERSONAL]
    if task_root is not None:
        ordered.append(Path(task_root) / "auth.env")
    if override is not None:
        ordered.append(Path(override))

    merged: dict[str, str] = {}
    for path in ordered:
        merged.update(_parse_env(path))

    if not merged.get("COOKIE"):
        raise SystemExit(
            "COOKIE missing. Sign in via Discogs-Bot Chrome, then run "
            "`python3 /home/box/discogs-auth/export_cookies.py` "
            "or save Cookie into /home/box/discogs-auth/auth.env."
        )
    return merged


def get_username(auth: dict[str, str] | None = None) -> str:
    data = auth if auth is not None else load_auth()
    user = (data.get("USERNAME") or "").strip()
    if not user:
        raise SystemExit(
            "USERNAME missing. Set it in /home/box/discogs-auth/personal.env "
            "(never put it in the bot persona)."
        )
    return user
