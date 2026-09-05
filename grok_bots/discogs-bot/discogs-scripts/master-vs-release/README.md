# master-vs-release

Wave 3 — master summary + all versions; highlight a given release among pressings.

## Endpoints

- Public: `GET /releases/{id}` → `master_id`; `GET /masters/{id}`; `GET /masters/{id}/versions`
- Optional session: GraphQL `DeferredReleaseData` sha `520dd540…cff7220` (vars `{discogsId}`) for `masterRelease` if public `master_id` missing

User-Agent for public API: `DiscogsScripts/1.0`. See `capture/SOURCE.md`.

## CLI

```bash
cd /workspace/discogs-scripts
python3 master-vs-release/scripts/master_vs_release.py --release-id 18197845
python3 master-vs-release/scripts/master_vs_release.py --master-id 4253358
```
