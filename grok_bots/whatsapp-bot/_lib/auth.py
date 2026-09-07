"""Load WhatsApp Web session from box-local auth.env (+ personal.env). Never print secrets."""
from __future__ import annotations

import os
from pathlib import Path

from _lib.envfile import merge_env, parse_env
from _lib.errors import WhatsAppAuthError

ROOT = Path(__file__).resolve().parents[1]
AUTH_PTR = ROOT / "_auth" / "AUTH_PATH.txt"
PERSONAL_PTR = ROOT / "_auth" / "PERSONAL_PATH.txt"

DEFAULT_AUTH_ENV = Path("/home/box/whatsapp-auth/auth.env")
DEFAULT_PERSONAL_ENV = Path("/home/box/whatsapp-auth/personal.env")


def auth_env_path() -> Path:
    """Cookie jar path: _auth/AUTH_PATH.txt pointer wins over the box default."""
    return Path(AUTH_PTR.read_text().strip()) if AUTH_PTR.exists() else DEFAULT_AUTH_ENV


def personal_env_path() -> Path:
    """Non-secret personal overrides path."""
    return Path(PERSONAL_PTR.read_text().strip()) if PERSONAL_PTR.exists() else DEFAULT_PERSONAL_ENV


# Kept for existing callers; the parser lives in _lib.envfile (shared file).
_load_env = parse_env


def load() -> dict[str, str]:
    """Merge auth.env -> personal.env -> WA_* environment. Later wins."""
    env = merge_env(auth_env_path(), personal_env_path())
    env.update({k: v for k, v in os.environ.items() if k.startswith("WA_")})
    return env


def require_cookie() -> str:
    env = load()
    c = env.get("COOKIE") or env.get("WA_COOKIE")
    if not c:
        raise WhatsAppAuthError(
            f"COOKIE missing (looked in {auth_env_path()}) — run QR link + export "
            "(see PLAN.md). Never paste cookies in chat."
        )
    return c
