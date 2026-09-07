# messages-read

Wave 1 — read last N messages in a named chat or JID.

## Args
- `--chat` name or jid (required)
- `--limit N` (default 20)
- `--mode` browser|http (default browser)

## Modes
Same opaque gate as chats-list: HTTP exits 2 until `capture/endpoints.json` has real URLs.

## CLI
```bash
python3 messages-read/scripts/read_messages.py --chat "Alice" --limit 20
python3 messages-read/scripts/read_messages.py --chat "Alice" --mode=http
```
