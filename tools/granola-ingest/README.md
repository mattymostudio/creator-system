# granola-ingest

Two-stage ingest: pull Granola meetings via MCP → dump raw JSON → (handoff) vault `/granola` slash command synthesizes into the rolling thematic archive.

## Why two stages

The Granola MCP only resolves inside a live Claude Code session — it can't be called from a standalone `.py`/`bash` script. So "the script" here is really a Claude-driven skill (see `.claude/SKILL.md`), and the work is split:

1. **Stage 1 (this tool)** — Claude pulls meetings via `mcp__granola__*` and dumps raw JSON to `tools/_outputs/granola/<date>-pull.json` + a manifest. No vault writes.
2. **Stage 2** — In a vault session, run `/granola <path-to-pull.json>`. The slash command reads the dump and synthesizes into `vault/03_SOURCE_NOTES/<year>/`.

The split means you can inspect the raw pull before it touches the vault, and rerun synthesis without repulling.

## Layout

```
granola-ingest/
├── README.md           # this file
├── .claude/
│   ├── SKILL.md        # the pull-step prompt
│   └── RECAP.md        # written after each run
└── (no _inputs)        # MCP is the input; no local raw files

../_outputs/granola/
├── 2026-04-17-pull.json
├── 2026-04-17-manifest.md
└── ...
```

## Standalone vs. vault-aware

Unlike the other tools in this kit, **granola-ingest has no meaningful
standalone path**. The Granola MCP only resolves inside a live Claude
Code session — there's no Python CLI to run. You need:

- **Granola** desktop app running and logged in
- **Granola MCP server** configured in your Claude Code settings
- **Claude Code** session open in a folder where Granola MCP is available

If you just want to see what the output looks like, open any sample
`*-pull.json` file — they're plain JSON and readable without running
anything.

## Usage

**From a Claude Code session** where the Granola MCP is available:

```
Run the granola-ingest pull step.
```

Claude follows `.claude/SKILL.md` — finds the last archive's
high-water mark, calls `mcp__granola__list_meetings`, batches
`mcp__granola__get_meetings`, writes the JSON + manifest, then prompts
you to switch into a vault session and run `/granola <pull-path>`.

Path A users (vault set up): the second stage writes synthesized notes
into `vault/03_SOURCE_NOTES/<year>/`. Re-running the pull step is
incremental — it only fetches meetings newer than the last high-water
mark.

Path B users (no vault): you can still do stage 1 (the pull) and end up
with a local JSON dump of your meeting notes. Stage 2 requires the
vault.

## Smoke test

```
Do a dry-run pull: don't write any files, just report how many new meetings exist and their titles.
```

## Verification

After a full run:
- `ls ../_outputs/granola/` — confirm dated JSON + manifest present
- Open the manifest — sanity-check titles, dates, participant counts
- `vault/03_SOURCE_NOTES/<year>/` — confirm the archive note extended or new archive created
- `vault/00_HOME/Log.md` — confirm a log entry was appended
- `tools/_shared/check-broken-paths.sh` — should exit 0

## Also referenced by

- `~/.claude/scheduled-tasks/granola-ingest/SKILL.md` — the scheduled-task wrapper that orchestrates stage 1 + stage 2
- `vault/.claude/commands/granola.md` — the stage 2 synthesis command

## Canon updates

This tool does NOT update canon pages (`04_CANON/`). The archive flags "pages to update / new page needed" at the bottom. Canon maintenance happens via `/enrich` or `/vault-lint` in a separate pass.
