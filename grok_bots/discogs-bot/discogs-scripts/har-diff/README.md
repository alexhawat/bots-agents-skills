# har-diff

Wave 5 — compare a HAR or `curls.txt` against known GraphQL `operationName` → `sha256Hash` fixtures (Wave 1–4).

## Fixture

`fixtures/known-operations.json` — at least:

- ViewerCollectionListData
- AddReleasesToWantlist / RemoveReleasesFromWantlist
- AddReleaseToCollection / RemoveReleaseFromCollection
- EditCollectionItemNote / RemoveCollectionItemNote

Self-test sample: `fixtures/sample-curls.txt`.

## CLI

```bash
cd discogs-scripts
uv run python har-diff/scripts/diff.py har-diff/fixtures/sample-curls.txt
uv run python har-diff/scripts/diff.py wantlist-add-remove/capture/curls.txt
uv run python har-diff/scripts/diff.py path/to.har --fixture har-diff/fixtures/known-operations.json
```

Reports: matched, drifted (same name, different hash), new ops, missing expected.

Exit **0** if no hash drift on known names; exit **1** if any known name drifted.
(Missing hashes / PLACEHOLDER captures count as missing, not drift.)
