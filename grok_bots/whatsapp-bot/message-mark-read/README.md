# message-mark-read

Wave 2 — mark a chat as read. Confirm-gated.

## Args
- `--chat` (required)
- `--confirm` — without it: dry-run only
- `--mode` browser|http

## CLI
```bash
python3 message-mark-read/scripts/mark_read.py --chat test
python3 message-mark-read/scripts/mark_read.py --chat test --confirm
```
