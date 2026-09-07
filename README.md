# bots-agents-skills

Reusable building blocks for agentic workflows.

| Kind | What lives here |
|------|-----------------|
| **Grok Bots** | Shareable bot personas and setups |
| **Agents** | Agent configs for Claude Code and Cursor |
| **Skills** | Portable skills those bots and agents can run |

Each package should be self-contained and documented enough to drop into another workspace.

### Grok Bots
- [`grok_bots/discogs-bot`](grok_bots/discogs-bot/) — Discogs automation bot (persona, skill, scripts). Copy scripts to `/workspace/discogs-scripts/` and auth helpers to `/home/box/discogs-auth/`.
- [`grok_bots/whatsapp-bot`](grok_bots/whatsapp-bot/) — WhatsApp Web automation bot (persona, skill, scripts). Copy pack to `/workspace/whatsapp-scripts/`; auth jar + exporters at `/home/box/whatsapp-auth/` (never ship live `auth.env`).

## License

MIT (unless a subdirectory says otherwise).
