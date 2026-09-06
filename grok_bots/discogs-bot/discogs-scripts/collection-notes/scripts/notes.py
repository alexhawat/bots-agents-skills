#!/usr/bin/env python3
"""Set or clear notes on a Discogs collection item.

Ops from wave4.har:
  EditCollectionItemNote   sha 75919451…
    vars {input:{discogsItemId, discogsNoteTypeId, noteText}}
  RemoveCollectionItemNote sha 098c6c80…
    vars {input:{discogsId}}  # note id

Note type ids (collection):
  1 = Media
  2 = Sleeve
  3 = free text / custom — capture used type 3 with noteText "wave4-temp"

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

EDIT_SHA = "759194518a1e8634735edc1b68d5c511b467fd1901249a7ac7d2d8387f7899db"
CLEAR_SHA = "098c6c80dd353a74a5263ac67fdc43637398940162e01d3ab034882263f050cd"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    set_p = sub.add_parser("set", help="Edit/set a collection item note")
    set_p.add_argument("--item-id", type=int, required=True, help="collection item id")
    set_p.add_argument(
        "--note-type-id",
        type=int,
        required=True,
        help="1=Media, 2=Sleeve, 3=free text (capture used 3)",
    )
    set_p.add_argument("--text", required=True)
    set_p.add_argument("--confirm", action="store_true")

    clr = sub.add_parser("clear", help="Remove a note by note id")
    clr.add_argument("--note-id", type=int, required=True)
    clr.add_argument("--confirm", action="store_true")

    args = ap.parse_args()

    if args.cmd == "set":
        op, sha = "EditCollectionItemNote", EDIT_SHA
        variables = {
            "input": {
                "discogsItemId": args.item_id,
                "discogsNoteTypeId": args.note_type_id,
                "noteText": args.text,
            }
        }
    else:
        op, sha = "RemoveCollectionItemNote", CLEAR_SHA
        variables = {"input": {"discogsId": args.note_id}}

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
