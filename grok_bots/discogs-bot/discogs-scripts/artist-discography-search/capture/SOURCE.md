# Capture notes — artist-discography-search

- Date: 2026-09-05
- Artist resolve: same autocomplete as barcode-or-catno-lookup (`GET /service/search-component/public/api/autocomplete`, see that task’s HAR).
- Discography: **documented public API** — `GET https://api.discogs.com/artists/{id}/releases` (Discogs API docs; User-Agent `DiscogsScripts/1.0`). No session Cookie required for this step.
- Sample verify: artist `Osvaldo Pugliese` → id `777492`.
