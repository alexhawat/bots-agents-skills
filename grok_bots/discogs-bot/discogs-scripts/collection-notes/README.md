# collection-notes

Wave 4 — mutate. LIVE 2026-09-05.

## Endpoints

POST `https://www.discogs.com/service/catalog/api/graphql`

| Op | sha256 | variables |
|----|--------|-----------|
| `EditCollectionItemNote` | `759194518a1e8634735edc1b68d5c511b467fd1901249a7ac7d2d8387f7899db` | `{"input":{"discogsItemId":itemId,"discogsNoteTypeId":typeId,"noteText":text}}` |
| `RemoveCollectionItemNote` | `098c6c80dd353a74a5263ac67fdc43637398940162e01d3ab034882263f050cd` | `{"input":{"discogsId": noteId }}` |

### Note type ids

| id | meaning |
|----|---------|
| 1 | Media |
| 2 | Sleeve |
| 3 | Free text / custom — **capture used type 3** with `noteText: "wave4-temp"` |

Capture: `../../wantlist-add-remove/capture/wave4.har`. See `capture/SOURCE.md`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie.

## CLI

```bash
cd discogs-scripts
uv run python collection-notes/scripts/notes.py set --item-id N --note-type-id 3 --text 'hello'
uv run python collection-notes/scripts/notes.py clear --note-id N
# live
uv run python collection-notes/scripts/notes.py set --item-id N --note-type-id 3 --text 'hello' --confirm
uv run python collection-notes/scripts/notes.py clear --note-id N --confirm
```
