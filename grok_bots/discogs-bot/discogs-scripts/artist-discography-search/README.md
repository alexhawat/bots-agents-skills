# artist-discography-search

Wave 3 — artist masters/releases via documented public API.

## Endpoints

1. Resolve artist: site autocomplete `_lib.discogs_search.autocomplete` (`search_type=ARTIST`), or pass `--artist-id`.
2. Discography: `GET https://api.discogs.com/artists/{id}/releases?sort=year&sort_order=desc&page=&per_page=` with User-Agent `DiscogsScripts/1.0`.

See `capture/SOURCE.md`.

## CLI

```bash
cd discogs-scripts
uv run python artist-discography-search/scripts/discography.py 'Osvaldo Pugliese' --per-page 5
uv run python artist-discography-search/scripts/discography.py --artist-id 777492 --page 1 --per-page 20 --role Main
```

Prints: `id`, `type`, `title`, `year`, `format`, `role` (tab-separated).
