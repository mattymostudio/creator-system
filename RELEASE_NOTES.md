# Creator System v2026-07-03

> **Personal Intelligence System for creative professionals** — open-source, MIT-licensed, runs locally on Obsidian + Claude Code or Codex. Built by [Matty Mo Studio](https://themostfamousartist.com).

Second release. Three headline additions since v2026-05-01: a community-contributed `/voice` skill generator, a full Codex compatibility layer, and a new curation tool for picking canonical work images. Skill count 14 → 15, tool count 6 → 7, recipes 23 → 24.

---

## What's new

### `/voice` — personal writing-voice skill generator

Contributed by **Adam Mischke ([@vanities](https://github.com/vanities))** — the first outside contribution to the kit.

Generates a `{slug}-voice` skill from the vault owner's own first-person sources in `02_SOURCES/`:

- Inventories your authored writing and separates it from press/summaries
- Detects surfaces (essay, social, transcript…) and proposes voice modes — with an approval gate before generating
- Measures a quantitative fingerprint (sentence length, signature punctuation, paragraph rhythm) — corrects folk beliefs about your own style with data
- Extracts vocabulary signatures, sentence patterns, verbatim calibration samples, and anti-sample pairs (generic-AI ❌ vs you ✅)
- Emits a `SKILL.md` from the new `Template - Voice Skill.md`, symlinked to `~/.claude/skills/` for global use
- Refresh mode re-runs only over new material and preserves hand-edits

### Codex compatibility

The kit now runs on OpenAI Codex as well as Claude Code:

- `AGENTS.md` (repo root) + `vault/AGENTS.md` — Codex operating instructions mirroring `CLAUDE.md`
- `.agents/skills/creator-system-vault/SKILL.md` — repo-scoped Codex skill mapping natural language and `/command` names to vault workflows
- `docs/CODEX.md` — setup, usage, and validation notes
- `scripts/check-codex-readiness.sh` + CI workflow keeping the layer consistent

### `work-hero-picker` — one canonical image per work (`tools/`)

The seventh tool, and the first *curation* tool: when your archive keeps a folder per work with several photos of the same piece, it builds a self-contained HTML picker (candidates auto-ranked, likely hero first), you click through, and it applies your picks as `_hero/` symlinks — originals never moved. Downstream site builders and catalog generators can rely on `_hero/` holding exactly one image per work. Recipe 24 in `RECIPES.md`.

---

## What's in the kit

- **Vault scaffolding** — 10-folder layered structure (sources → source notes → canon → outputs), hub pages, templates, and the vault constitution at `10_META/AGENTS.md`
- **15 AI skills** (`vault/.claude/commands/`) — ingestion (`/ingest`, `/granola`), synthesis (`/diarize`, `/enrich`, `/emerge`, `/connect`), analysis (`/challenge`, `/drift`, `/council`, `/ideas`), maintenance (`/vault-lint`, `/improve`, `/recap`), research (`/autoresearch`), and now `/voice`
- **7 tools** (`tools/`) — photo-processor, takeout-processor, chatgpt-ingest, facebook-ingest, press-ingest, granola-ingest, work-hero-picker
- **Docs** — `README.md`, `RECIPES.md` (24 recipes), `Standard Operating Procedure.md`, `Data Sources to Gather.md`

Full history in [`CHANGELOG.md`](CHANGELOG.md).

---

## How to use it

1. **Get the kit** — clone via git or Download ZIP, unzip wherever you keep projects.
2. **Install** [Obsidian](https://obsidian.md) and an AI coding agent — Claude Code or Codex.
3. **Open your agent at this folder and type `let's go`** — onboarding starts automatically.

Total: ~10 minutes to a working personal intelligence system you own. Your data stays on your laptop in plain text.

---

## License & ownership

MIT — see [`LICENSE`](LICENSE). Your data is yours. Your custom skills and canon pages stay private unless you choose to share. The kit ships as a starting point; you take it from there.
