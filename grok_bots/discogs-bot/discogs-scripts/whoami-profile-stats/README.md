# whoami / profile-stats

Wave 3 — signed-in identity, folder counts, optional collection value snapshot.

## Endpoints

| Op | sha256 | vars |
|----|--------|------|
| `UserCollectionPageData` | `4ec9e7cf…1cd96` | `{username}` |
| `ViewerCollectionListData` | `91302e22…0dda9` | page/perPage/folderId/search… |
| `ViewerCollectionPageData` | `462fbd5e…4a2b7` | `{currency}` (HAR 2026-11-05; was `{currency, search}`) |

Captured 2026-09-05 in `collection-search/capture/collection-federico.har`. See `capture/SOURCE.md`.

If `ViewerCollectionPageData` fails (hash drift), the script skips value stats and notes it.

## Auth

`/home/box/discogs-auth/auth.env` + `personal.env` via `_lib/auth.py` — never print Cookie. `USERNAME` required (personal.env canonical; `--username` CLI override).

## CLI

```bash
cd discogs-scripts
uv run python whoami-profile-stats/scripts/whoami.py
uv run python whoami-profile-stats/scripts/whoami.py --json
uv run python whoami-profile-stats/scripts/whoami.py --username "$USERNAME" --json
uv run python whoami-profile-stats/scripts/whoami.py --skip-value
```
