# message-send

Wave 2 — send a text message to a chat. **Confirm-gated. No bulk/spam tooling.**

## Args
- `--chat` (required)
- `--text` (required)
- `--confirm` — without it: **dry-run only** (print plan, exit 0, no action)
- `--mode` browser|http (default browser)

## Behavior
| flags | result |
| --- | --- |
| no `--confirm` | dry-run: print what would send; exit 0 |
| `--confirm` + browser | print browserUse steps to send once |
| `--confirm` + http | TRAFFIC_OPAQUE exit 2 until capture |

## CLI
```bash
python3 message-send/scripts/send.py --chat test --text hi          # dry-run
python3 message-send/scripts/send.py --chat test --text hi --confirm
```
