# har-diff

Wave 4 — compare a HAR or URL list against `capture/expected-urls.json`.

Adapted lightly from Discogs `har-diff`, but WhatsApp has no GraphQL operation hashes — we compare **URL host+path** sets only.

## Rules
- Never print Cookie / Authorization / token header values (headers are stripped from reports).
- `expected-urls.json` starts with `"urls": []` until captures fill it.

## CLI
```bash
cd /workspace/whatsapp-scripts
python3 har-diff/scripts/diff.py har-diff/fixtures/sample-urls.txt
python3 har-diff/scripts/diff.py path/to.har
python3 har-diff/scripts/diff.py path/to.har --expected har-diff/capture/expected-urls.json
```

Exit **0** if no unexpected drift policy failure (missing expected still OK when expected is empty); exit **1** if an expected URL is missing from the capture when expected list is non-empty.
