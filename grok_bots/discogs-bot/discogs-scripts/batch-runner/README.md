# batch-runner

Wave 5 — thin CLI wrapping existing search scripts (subprocess).

## Mapping

| subcommand | script |
|------------|--------|
| `search collection` | `collection-search/scripts/search_collection.py` |
| `search wantlist` | `mywantlist-search/scripts/search.py` |
| `search market` | `marketplace-search/scripts/search.py` |

## CLI

```bash
cd discogs-scripts
uv run python batch-runner/scripts/batch.py search collection --q kraftwerk --vinyl-only
uv run python batch-runner/scripts/batch.py search wantlist --q aphex
uv run python batch-runner/scripts/batch.py search market --q "basic channel" --format Vinyl --currency EUR
```

Prints `# invoked <script-path>` then the child script’s stdout. Exit code = child exit code.
Auth is handled by each child via `/home/box/discogs-auth/auth.env`.
