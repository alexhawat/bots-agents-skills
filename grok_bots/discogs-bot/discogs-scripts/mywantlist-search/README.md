# mywantlist-search

Search the real Discogs wantlist UI at `https://www.discogs.com/mywantlist`.

## Capture (2026-09-05)

- HTML list pages: `GET /mywantlist?search={q}&page={n}`
- No dedicated GraphQL list XHR observed; rows are `tr.wantlist_r{releaseId}`
- Auth: `/home/box/discogs-auth/auth.env`

Unlike Wave 1 `wantlist-search` (marketplace wantlist-for-sale / `sell_item`), this is the **actual wantlist**.

## CLI

```bash
cd discogs-scripts
uv run python mywantlist-search/scripts/search.py 'Domingo Federico'
uv run python mywantlist-search/scripts/search.py 'Domingo Federico' --artist-match Federico
```
