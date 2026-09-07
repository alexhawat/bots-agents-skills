"""Load WhatsApp Web session from box-local auth.env (+ optional personal.env). Never print secrets."""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH_PTR = ROOT / "_auth" / "AUTH_PATH.txt"
PERSONAL_PTR = ROOT / "_auth" / "PERSONAL_PATH.txt"


def _load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load() -> dict[str, str]:
    auth_path = Path(AUTH_PTR.read_text().strip()) if AUTH_PTR.exists() else Path("/home/box/whatsapp-auth/auth.env")
    personal_path = Path(PERSONAL_PTR.read_text().strip()) if PERSONAL_PTR.exists() else Path("/home/box/whatsapp-auth/personal.env")
    env = {}
    env.update(_load_env(auth_path))
    env.update(_load_env(personal_path))
    env.update({k: v for k, v in os.environ.items() if k.startswith("WA_")})
    return env


def require_cookie() -> str:
    env = load()
    c = env.get("COOKIE") or env.get("WA_COOKIE")
    if not c:
        raise SystemExit("No COOKIE in auth.env — run QR link + export (see PLAN.md). Never paste cookies in chat.")
    return c
