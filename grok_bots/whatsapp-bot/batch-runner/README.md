# batch-runner

Wave 4 — run a named list of **read-only** scripts from a JSON or YAML batch file.

## Allowed slugs (read-only)
`auth-check`, `chats-list`, `messages-read`, `chats-search`, `contact-info`, `har-diff`, `media-download` (browser-doc only).

Mutating slugs (`message-send`, `message-mark-read`) are **rejected** by the runner.

## CLI
```bash
cd /workspace/whatsapp-scripts
python3 batch-runner/scripts/batch.py batch-runner/fixtures/sample-batch.json
python3 batch-runner/scripts/batch.py batch-runner/fixtures/sample-batch.yaml
```

Prints each invoked script path (no secrets). Exit code = first non-zero child, or 0 if all succeed.
