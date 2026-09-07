# media-download

Wave 3 — download media for a message id. Opaque until capture.

## Args
- `--message-id` (required)
- `--out` output path (required)
- `--mode` browser|http

## CLI
```bash
python3 media-download/scripts/download.py --message-id MSGID --out /tmp/wa-media.bin
python3 media-download/scripts/download.py --message-id MSGID --out /tmp/x.bin --mode=http
```
