# Creator System v2026-05-01

> **Initial public release.** Personal Intelligence System for creative professionals — open-source, MIT-licensed, runs locally on Obsidian + Claude Code. Built by [Matty Mo Studio](https://themostfamousartist.com).

A structured, AI-augmented knowledge system for creators with multi-domain practices — artists, designers, musicians, filmmakers, writers, builders, anyone with a scattered archive worth synthesizing.

This release is the version distributed to Cohort 01 of the Creator System cohort program. Early — actively used, actively shaped by friction logs from the cohort.

---

## Why this exists

Most AI tools wrap a chatbot around a prompt. This wraps a chatbot around your archive.

The vault is structured (sources → source notes → canon → outputs) and trust-aware (journals win for emotional truth; business docs for what actually happened; press for what others *think* happened). Skills compose across the layers to produce outputs that sound like *you* because they *are* you — synthesized from your own material, not the average of the internet.

---

## What's in this release

### Vault scaffolding (`vault/`)

10-folder layered structure with hub pages, page templates, and the vault constitution (`10_META/AGENTS.md`):

- `00_HOME/` · navigation hubs, log, open questions
- `01_INBOX/` · drop zone for unprocessed material
- `02_SOURCES/` · raw, immutable source material
- `03_SOURCE_NOTES/` · processed extracts
- `04_CANON/` · durable synthesized knowledge
- `05_PROJECTS/` · execution tracking
- `06_OUTPUTS/` · reusable deliverables
- `08_RESEARCH/` · external-topic knowledge
- `09_IDEAS/` · experimental concepts
- `10_META/` · system rules + templates

### 14 AI skills (`vault/.claude/commands/`)

| Command | Function |
|---|---|
| `/ingest` | Process a raw source through the full vault pipeline |
| `/diarize` | Build a comprehensive canon page from all sources about a subject |
| `/enrich` | Fill out a thin canon page by finding all related sources |
| `/vault-lint` | Run 10 structural checks and write a report |
| `/improve` | Analyze patterns and propose system improvements |
| `/recap` | Close a session with a dated entry in `00_HOME/Log.md` |
| `/autoresearch` | Autonomous external-topic research loop |
| `/granola` | Synthesize Granola meeting pulls into the rolling archive |
| `/emerge` | Surface ideas the vault implies but never stated |
| `/challenge` | Pressure-test a belief against the vault's own evidence |
| `/connect` | Find hidden bridges between two topics |
| `/drift` | Compare stated priorities vs actual activity |
| `/ideas` | Vault-wide brainstorm grounded in what the vault knows |
| `/council` | 12 professional personas evaluate a project, idea, or deal |

You don't need to type the slash — plain English works just as well.

### 6 ingestion pipelines (`tools/`)

Each one takes a messy export from a platform you already use and turns it into plain-text Markdown that lands in your vault.

| Tool | Input | Output |
|---|---|---|
| `photo-processor` | iPhone photo dump | events · faces · locations |
| `takeout-processor` | Google Takeout | contacts · timeline · relationships |
| `chatgpt-ingest` | ChatGPT export | topic index |
| `facebook-ingest` | Facebook archive | message threads + contacts |
| `press-ingest` | Press URLs | cleaned local article archive |
| `granola-ingest` | Granola meetings | rolling source-note (pairs with `/granola` skill) |

### Documentation

- `README.md` · front-door overview, quick start
- `CLAUDE.md` · instructions for Claude Code (read on every fresh session)
- `RECIPES.md` · 23 step-by-step recipes (input → tool → skill → output) by data type
- `Standard Operating Procedure.md` · daily use, weekly maintenance, manual fallbacks
- `Data Sources to Gather.md` · what raw materials to collect and where each type goes
- `vault/10_META/AGENTS.md` · the vault constitution

---

## How to use it

1. **Get the kit** — clone via git or Download ZIP, unzip wherever you keep projects.
2. **Install** [Obsidian](https://obsidian.md) and [Claude Code](https://claude.ai/claude-code).
3. **Open Claude Code, point it at this folder, type `let's go`** — onboarding starts automatically.

Total: ~10 minutes to a working personal intelligence system you own. Your data stays on your laptop in plain text. The kit is yours to keep, modify, fork — MIT license.

---

## License & ownership

MIT — see [`LICENSE`](LICENSE). Your data is yours. Your custom skills and canon pages stay private unless you choose to share. The kit ships as a starting point; you take it from there.
