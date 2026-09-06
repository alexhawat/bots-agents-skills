#!/usr/bin/env python3
"""Export Discogs session Cookie → auth.env (0600).

Source order, first hit wins:
  1. live CDP jar from this display  (export_from_display.mjs)
  2. box cookie seed                 (chrome-cookie-seed.json)
  3. Chrome SQLite decrypt           (best effort; usually no os_crypt key here)

Destination is $DISCOGS_AUTH_ENV, else $DISCOGS_AUTH_DIR/auth.env, else the
box default. Never prints cookie values. Exit 0 on success, 1 on failure.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import sqlite3
import tempfile
from hashlib import pbkdf2_hmac
from pathlib import Path

DEFAULT_AUTH_DIR = "/home/box/discogs-auth"
DEFAULT_SEED = "/home/box/agent-data/chrome-cookie-seed.json"
DEFAULT_WORK = "/workspace/discogs-scripts/_auth"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


# Resolved per call, not at import: a caller that sets DISCOGS_* after importing
# this module (tests, wrappers) must still get the path it asked for.
def out_path() -> Path:
    """Match _lib.auth resolution so exporter and loader never disagree."""
    if os.environ.get("DISCOGS_AUTH_ENV"):
        return Path(os.environ["DISCOGS_AUTH_ENV"])
    return Path(os.environ.get("DISCOGS_AUTH_DIR") or DEFAULT_AUTH_DIR) / "auth.env"


def seed_path() -> Path:
    return Path(os.environ.get("DISCOGS_COOKIE_SEED") or DEFAULT_SEED)


def work_dir() -> Path:
    return Path(os.environ.get("DISCOGS_WORK_AUTH") or DEFAULT_WORK)


def write_secret(path: Path, text: str) -> None:
    """Create `path` at mode 0600 *before* writing.

    write_text() would create at the umask default (0644) and leave the cookie
    world-readable until the chmod landed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(path, 0o600)  # tighten if the file already existed more openly


def _write(parts: list[str], names: list[str], source: str) -> int:
    out = out_path()
    write_secret(out, f"COOKIE={'; '.join(parts)}\nUSER_AGENT={UA}\n")
    # Write only the POINTER into the work tree — never a copy of the jar.
    # Consumers resolve the real path via _lib.auth, so a duplicate secret
    # inside the repo checkout would be pure risk with no reader.
    work = work_dir()
    work.mkdir(parents=True, exist_ok=True)
    (work / "AUTH_PATH.txt").write_text(str(out) + "\n")
    print(f"ok source={source} cookies={len(names)} names={sorted(set(names))} path={out}")
    return 0



def export_from_this_display() -> int | None:
    """Live jar from this agent's Chrome via official sand-host CDP helper."""
    import subprocess
    helper = Path(__file__).resolve().parent / "export_from_display.mjs"
    if not helper.is_file():
        return None
    r = subprocess.run(
        ["node", "--experimental-websocket", str(helper)],
        capture_output=True,
        text=True,
    )
    if r.stdout:
        print(r.stdout.rstrip())
    if r.returncode == 0:
        return 0
    return None

def export_from_seed() -> int | None:
    seed = seed_path()
    if not seed.is_file():
        return None
    try:
        data = json.loads(seed.read_text())
    except Exception:
        return None
    rows = [c for c in (data.get("cookies") or []) if "discogs" in (c.get("domain") or "").lower()]
    # last write wins per name; prefer names with values
    by_name: dict[str, str] = {}
    for c in rows:
        name = c.get("name") or ""
        val = c.get("value") or ""
        if not name or not val:
            continue
        by_name[name] = val
    names = list(by_name)
    if "session" not in by_name and "sid" not in by_name:
        return None
    parts = [f"{n}={by_name[n]}" for n in names]
    return _write(parts, names, f"seed:{seed}")


def profiles():
    root = Path("/home/box")
    profiles_glob = root.glob("chrome-profile*/Default/Cookies")
    for p in sorted(profiles_glob, key=lambda x: x.stat().st_mtime, reverse=True):
        yield p.parent.parent


def load_key(profile: Path):
    ls = profile / "Local State"
    if not ls.exists():
        return None
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except ImportError:
        return None
    enc = json.loads(ls.read_text()).get("os_crypt", {}).get("encrypted_key")
    if not enc:
        return None
    raw = base64.b64decode(enc)
    if raw.startswith(b"ChromeSafeStorage"):
        raw = raw[len(b"ChromeSafeStorage") :]
    keys = [pbkdf2_hmac("sha1", b"", b"saltysalt", 1, dklen=16)]
    if len(raw) in (16, 32):
        keys.append(raw)
    return keys


def decrypt(key: bytes, data: bytes):
    if not data or data[:3] not in (b"v10", b"v11"):
        return None
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(data[3:15], data[15:], None)
    except Exception:
        return None


def export_from(profile: Path, keys):
    db = profile / "Default" / "Cookies"
    if not db.exists():
        return None
    # mkstemp, not mktemp: this copy holds the live cookie DB, and a
    # predictable name is a symlink-race waiting to happen.
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        shutil.copy2(db, tmp)
        con = sqlite3.connect(tmp)
        try:
            rows = con.execute(
                "select name, encrypted_value, value from cookies "
                "where host_key like '%discogs%'"
            ).fetchall()
        finally:
            con.close()
    finally:
        os.unlink(tmp)
    for key in keys:
        parts, names = [], []
        for name, enc, val in rows:
            plain = None
            if isinstance(val, str) and val:
                plain = val.encode()
            elif isinstance(val, bytes) and val:
                plain = val
            elif enc:
                plain = decrypt(key, enc if isinstance(enc, bytes) else bytes(enc))
            if not plain:
                continue
            try:
                s = plain.decode("utf-8")
            except Exception:
                continue
            parts.append(f"{name}={s}")
            names.append(name)
        if "session" in names or "sid" in names:
            return parts, names
    return None


def main() -> int:
    live = export_from_this_display()
    if live is not None:
        return live
    got = export_from_seed()
    if got is not None:
        return got
    out_path().parent.mkdir(parents=True, exist_ok=True)
    for profile in profiles():
        keys = load_key(profile)
        if not keys:
            continue
        gotp = export_from(profile, keys)
        if not gotp:
            continue
        parts, names = gotp
        return _write(parts, names, f"profile:{profile.name}")
    print(
        "fail: no discogs session in chrome-cookie-seed.json and could not decrypt "
        "chrome-profile* Cookies. Sign in via Discogs-Bot Chrome, wait for "
        "sand-cookie-persist to refresh the seed, then re-run this script."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
