# whoami / profile-stats

Wave 3 — signed-in identity, folder counts, optional collection value snapshot.

## Endpoints

| Op | sha256 | vars |
|----|--------|------|
| `UserCollectionPageData` | `4ec9e7cf…1cd96` | `{username}` |
| `ViewerCollectionListData` | `ebc71d10…835f1b` | page/perPage/folderId/search… |
| `ViewerCollectionPageData` | `462fbd5e…4a2b7` | `{currency, search}` (search `""` for full-collection stats) |

Captured 2026-09-05 in `collection-search/capture/collection-federico.har`. See `capture/SOURCE.md`.

If `ViewerCollectionPageData` fails (hash drift), the script skips value stats and notes it.

## Auth

`/home/box/discogs-auth/auth.env` + `personal.env` via `_lib/auth.py` — never print Cookie. `USERNAME` required (personal.env canonical; `--username` CLI override).

## CLI

```bash
cd /workspace/discogs-scripts
python3 whoami-profile-stats/scripts/whoami.py
python3 whoami-profile-stats/scripts/whoami.py --json
python3 whoami-profile-stats/scripts/whoami.py --username "$USERNAME" --json
python3 whoami-profile-stats/scripts/whoami.py --skip-value
```
