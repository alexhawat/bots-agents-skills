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

## License

MIT (unless a subdirectory says otherwise).
