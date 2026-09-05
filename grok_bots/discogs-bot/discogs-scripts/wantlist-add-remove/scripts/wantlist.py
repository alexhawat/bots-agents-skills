#!/usr/bin/env python3
"""Add or remove releases from the Discogs wantlist (GraphQL mutate).

Ops from wave4.har:
  AddReleasesToWantlist    sha d07fa55f…
  RemoveReleasesFromWantlist sha ab4a277f…

Without --confirm: print planned mutation and exit 2.
Never prints Cookie / secrets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from _lib.auth import load_auth  # noqa: E402
from _lib.errors import DiscogsAPIError, cli_main  # noqa: E402
from _lib.graphql_mutate import graphql_mutate, require_confirm  # noqa: E402

TASK = Path(__file__).resolve().parents[1]

ADD_SHA = "d07fa55f88404b5d0e5253faf962ed104ad1efd3af871c9281b76e874d4a2bf4"
REMOVE_SHA = "ab4a277f4c5d9da56ba17d4b88643c51a1935f500813133c55fe5a340625d06f"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    add_p = sub.add_parser("add", help="Add release(s) to wantlist")
    add_p.add_argument("--release-id", type=int, required=True, action="append")
    add_p.add_argument("--confirm", action="store_true")

    rm_p = sub.add_parser("remove", help="Remove release(s) from wantlist")
    rm_p.add_argument("--release-id", type=int, required=True, action="append")
    rm_p.add_argument("--confirm", action="store_true")

    args = ap.parse_args()
    ids = list(dict.fromkeys(args.release_id))  # preserve order, dedupe
    variables = {"input": {"releaseDiscogsIds": ids}}

    if args.cmd == "add":
        op, sha = "AddReleasesToWantlist", ADD_SHA
    else:
        op, sha = "RemoveReleasesFromWantlist", REMOVE_SHA

    planned = (
        f"# planned GraphQL POST mutate\n"
        f"# operationName={op}\n"
        f"# sha256Hash={sha}\n"
        f"# variables={json.dumps(variables, separators=(',', ':'))}\n"
        f"# endpoint=https://www.discogs.com/service/catalog/api/graphql"
    )
    require_confirm(args.confirm, planned)

    auth = load_auth(task_root=TASK)
    data = graphql_mutate(
        auth,
        operation_name=op,
        sha256_hash=sha,
        variables=variables,
    )
    if data.get("errors"):
        raise DiscogsAPIError(f"GraphQL errors ({op}): {data['errors']!r}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli_main(main)
