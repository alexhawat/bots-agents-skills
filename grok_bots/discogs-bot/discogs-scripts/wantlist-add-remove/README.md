# wantlist-add-remove

Wave 4 — mutate. LIVE 2026-09-05.

## Endpoints

POST `https://www.discogs.com/service/catalog/api/graphql`

| Op | sha256 | variables |
|----|--------|-----------|
| `AddReleasesToWantlist` | `d07fa55f88404b5d0e5253faf962ed104ad1efd3af871c9281b76e874d4a2bf4` | `{"input":{"releaseDiscogsIds":[ids]}}` |
| `RemoveReleasesFromWantlist` | `ab4a277f4c5d9da56ba17d4b88643c51a1935f500813133c55fe5a340625d06f` | `{"input":{"releaseDiscogsIds":[ids]}}` |

Capture: `capture/wave4.har` + `capture/curls.txt`. See `capture/SOURCE.md`.

## Auth

`$DISCOGS_AUTH_ENV` (default `/home/box/discogs-auth/auth.env`) — never print Cookie. Uses `_lib/auth.py` + `_lib/graphql_mutate.py`.

## CLI

```bash
cd discogs-scripts
# dry-run (exit 2)
uv run python wantlist-add-remove/scripts/wantlist.py add --release-id 2825456
uv run python wantlist-add-remove/scripts/wantlist.py remove --release-id 2825456
# live mutate
uv run python wantlist-add-remove/scripts/wantlist.py add --release-id 2825456 --confirm
uv run python wantlist-add-remove/scripts/wantlist.py remove --release-id 2825456 --confirm
```
