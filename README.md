# bots-agents-skills

Reusable building blocks for agentic workflows.

| Kind | What lives here |
|------|-----------------|
| **Grok Bots** | Canonical bot packs: persona + runnable script trees (single source of truth) |
| **Hermes** | Instruction-only packs for the Hermes Agent runtime |
| **OpenClaw** | Instruction-only skill packs for OpenClaw (ClawHub-style) |
| **Agents** | Agent configs for Claude Code and Cursor |
| **Skills** | Portable skills those bots and agents can run |

Each package should be self-contained and documented enough to drop into another workspace.

## Reference, don't copy

Runnable code exists **once**, under `grok_bots/` on the `main` branch. The
`hermes/` and `openclaw/` packs contain only persona/skill markdown that points
at a local clone (`BOTS_REPO_ROOT`, default `~/bots-agents-skills`) and runs the
scripts in place — a `git pull` is the update mechanism, and fixes land once for
every runtime. CI enforces the split: `tools/pack_drift_guard.py` fails the
build if any `.py`/`.mjs` file ever appears under `hermes/` or `openclaw/`.

## Bot × infra matrix

| Bot | Grok | Hermes | OpenClaw |
|-----|------|--------|----------|
| Discogs | [`grok_bots/discogs-bot`](grok_bots/discogs-bot/) | [`hermes/discogs-bot`](hermes/discogs-bot/) | [`openclaw/discogs-bot`](openclaw/discogs-bot/) |
| WhatsApp | [`grok_bots/whatsapp-bot`](grok_bots/whatsapp-bot/) | [`hermes/whatsapp-bot`](hermes/whatsapp-bot/) | [`openclaw/whatsapp-bot`](openclaw/whatsapp-bot/) |

### Grok Bots
- [`grok_bots/discogs-bot`](grok_bots/discogs-bot/) — Discogs automation bot (persona, skill, 27 stdlib-only Python scripts). Copy scripts to `/workspace/discogs-scripts/` and auth helpers to `/home/box/discogs-auth/`. Offline: `make check`.
- [`grok_bots/whatsapp-bot`](grok_bots/whatsapp-bot/) — WhatsApp Web automation bot (persona, skill, scripts; headless CDP via Node 20+). Copy pack to `/workspace/whatsapp-scripts/`; auth jar + exporters at `/home/box/whatsapp-auth/` (never ship live `auth.env`).

### Hermes / OpenClaw

Instruction-only packs. Install = clone this repo, export `BOTS_REPO_ROOT` plus
the bot's auth-dir override, drop the skill folder into the runtime. Each pack's
README has the exact steps.

## Repo management

- **CI**: per-pack workflows ([discogs](.github/workflows/discogs-bot.yml),
  [whatsapp](.github/workflows/whatsapp-bot.yml)) run ruff + pytest + secrets
  guards; [packs.yml](.github/workflows/packs.yml) runs the drift guard.
- **Advisory review**: [mergeCraft](https://github.com/alexhawat/mergeCraft)
  reviews every PR ([mergecraft.yml](.github/workflows/mergecraft.yml)) — never
  a merge gate; a clean advisory verdict earns an auto-approval
  ([mergecraft-approve.yml](.github/workflows/mergecraft-approve.yml)).
- **protect-main ruleset**: PRs required, no force pushes, no deletions.
- `make install-hooks` installs a pre-push guard refusing commits from
  authors outside [`.github/trusted-authors.txt`](.github/trusted-authors.txt).
- `make verify-discogs` / `make verify-whatsapp` check a local install on any
  runtime (clone present, auth jar in place; `PROBE=1` adds a live auth probe).
- Never commit live `auth.env` / `personal.env`, cookies, unredacted HARs, chat
  transcripts, or phone numbers.

## License

MIT (unless a subdirectory says otherwise).
