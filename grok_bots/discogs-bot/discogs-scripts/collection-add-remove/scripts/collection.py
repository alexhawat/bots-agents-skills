#!/usr/bin/env python3
"""Add a release to, or remove a collection ITEM from, the Discogs collection.

Ops from wave4.har:
  AddReleaseToCollection     sha 60200b3a…  vars {input:{discogsReleaseId}}
  RemoveReleaseFromCollection sha 93242d93… vars {input:{discogsId}}  # ITEM id

Capture sent no folderId on add — Discogs uses the account default folder
(typically Uncategorized / folder 1).

Remove uses collection ITEM id (not release id). Get it from
collection-export (`collection_item_id`) or UserReleaseData.

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

ADD_SHA = "60200b3acb935a2304a8b7eb19e6b480aa05ca656a24206d9ac41ca0d7c0aac9"
REMOVE_SHA = "93242d935addda589c5114a57e09b404213bdd55737fb6bdc2b91a6c3fe7337c"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    add_p = sub.add_parser("add", help="Add release to default collection folder")
    add_p.add_argument("--release-id", type=int, required=True)
    add_p.add_argument("--confirm", action="store_true")

    rm_p = sub.add_parser(
        "remove",
        help="Remove collection ITEM by item id (not release id)",
    )
    rm_p.add_argument(
        "--item-id",
        type=int,
        required=True,
        help="collection item discogsId (export: collection_item_id)",
    )
    rm_p.add_argument("--confirm", action="store_true")

    args = ap.parse_args()

    if args.cmd == "add":
        op, sha = "AddReleaseToCollection", ADD_SHA
        variables = {"input": {"discogsReleaseId": args.release_id}}
        note = (
            "# note: folderId not in capture — Discogs default folder is used"
        )
    else:
        op, sha = "RemoveReleaseFromCollection", REMOVE_SHA
        variables = {"input": {"discogsId": args.item_id}}
        note = "# note: discogsId is collection ITEM id, not release id"

    planned = (
        f"# planned GraphQL POST mutate\n"
        f"# operationName={op}\n"
        f"# sha256Hash={sha}\n"
        f"# variables={json.dumps(variables, separators=(',', ':'))}\n"
        f"# endpoint=https://www.discogs.com/service/catalog/api/graphql\n"
        f"{note}"
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
