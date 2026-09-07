"""HTTP replay gate: refuse invented WhatsApp endpoints until capture exists."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NoReturn


def endpoints_path(task_root: Path) -> Path:
    return task_root / "capture" / "endpoints.json"


def load_endpoints(task_root: Path) -> dict[str, Any]:
    path = endpoints_path(task_root)
    if not path.is_file():
        return {"status": "none", "endpoints": []}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"status": "none", "endpoints": []}
    if not isinstance(data, dict):
        return {"status": "none", "endpoints": []}
    eps = data.get("endpoints") or []
    if not isinstance(eps, list):
        eps = []
    return {"status": data.get("status", "none"), "endpoints": eps}


def has_real_endpoints(task_root: Path) -> bool:
    data = load_endpoints(task_root)
    if data.get("status") == "none":
        return False
    eps = data.get("endpoints") or []
    return any(isinstance(e, dict) and e.get("url") for e in eps)


def refuse_http(task_root: Path, slug: str) -> NoReturn:
    print(
        f"TRAFFIC_OPAQUE: {slug} has no captured HTTP endpoints "
        f"({endpoints_path(task_root)}). WhatsApp Web traffic is typically "
        f"WebSocket/protobuf — do not invent private API URLs. "
        f"Use --mode=browser and follow README/browserUse steps, or capture "
        f"real traffic into capture/endpoints.json first.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def require_http_or_exit(task_root: Path, slug: str) -> list[dict[str, Any]]:
    if not has_real_endpoints(task_root):
        refuse_http(task_root, slug)
    data = load_endpoints(task_root)
    return list(data["endpoints"])
