# collection-add-remove

Wave 4 — mutate. LIVE 2026-09-05.

## Endpoints

POST `https://www.discogs.com/service/catalog/api/graphql`

| Op | sha256 | variables |
|----|--------|-----------|
| `AddReleaseToCollection` | `60200b3acb935a2304a8b7eb19e6b480aa05ca656a24206d9ac41ca0d7c0aac9` | `{"input":{"discogsReleaseId":id}}` |
| `RemoveReleaseFromCollection` | `93242d935addda589c5114a57e09b404213bdd55737fb6bdc2b91a6c3fe7337c` | `{"input":{"discogsId": collectionItemId }}` |

**Add:** capture did not send a folder id — Discogs places the copy in the **default folder** (usually Uncategorized).

**Remove:** `discogsId` is the **collection item id**, not the release id. Obtain via:
- `collection-export` CSV/JSON column `collection_item_id`
- GraphQL `UserReleaseData` / collection list item `discogsId`

Capture: `capture/wave4.har` (same session as wantlist-add-remove). See `capture/SOURCE.md`.

## Auth

`/home/box/discogs-auth/auth.env` — never print Cookie.

## CLI

```bash
cd /workspace/discogs-scripts
python3 collection-add-remove/scripts/collection.py add --release-id 2825456
python3 collection-add-remove/scripts/collection.py remove --item-id 2181219053
# live
python3 collection-add-remove/scripts/collection.py add --release-id 2825456 --confirm
python3 collection-add-remove/scripts/collection.py remove --item-id 2181219053 --confirm
```
