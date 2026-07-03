# Creator System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Built by Matty Mo Studio](https://img.shields.io/badge/built%20by-Matty%20Mo%20Studio-ff3d8a.svg)](https://themostfamousartist.com)

> **Personal Intelligence System for creative professionals.** Open-source, MIT-licensed, runs locally on Obsidian + Claude Code or Codex. Vault scaffolding + 15 AI skills + 7 tools that turn your scattered archive into a queryable second brain.

Not a notes app. A layered system that archives source material, builds structured knowledge, tracks projects, and generates outputs — with AI-powered skills that do the heavy synthesis.

> *"Most AI tools wrap a chatbot around a prompt. This wraps a chatbot around your archive. Output sounds like you because it is you."*

---

## Quick start — three steps

### 1. Get the kit

```bash
git clone https://github.com/mattymostudio/creator-system.git
cd creator-system
```

Or **Code → Download ZIP** above, then unzip wherever you keep projects (`~/Documents/`, `~/code/`, anywhere). The folder you end up with **is your working vault** — no install step, no second copy.

### 2. Install Obsidian + an AI coding agent

- [Obsidian](https://obsidian.md) — free, the editor for your vault
- Claude Code — reads `CLAUDE.md` and the command specs in `vault/.claude/commands/`
- Codex — reads `AGENTS.md`, `vault/AGENTS.md`, and the repo skill in `.agents/skills/creator-system-vault/`

### 3. Open your agent at this folder and type `let's go`

Claude reads `CLAUDE.md`; Codex reads `AGENTS.md`. Either agent sees you're a fresh user and walks you through:

1. Personalizing the vault with your name + practice
2. Dropping your first source into `vault/01_INBOX/To Process/`
3. Running `/ingest` to process it
4. Running `/diarize` to build your first canon page
5. Initializing git so everything you do is undoable

Total: ~10 minutes to a working personal intelligence system you own.

> **Tip:** open this same folder in Obsidian alongside Claude Code. You'll see the markdown files Claude is writing in real time, and you can edit any of them directly.

---

## What's in here

```
creator-system/                  ← you're here; this IS your vault
├── vault/                       ← 10-folder layered knowledge system
│   ├── .claude/commands/        ← 15 Claude Code command specs
│   ├── AGENTS.md                ← Codex vault-level operating instructions
│   ├── 00_HOME/                 ← Navigation hubs and system state
│   ├── 01_INBOX/                ← Drop new material here
│   ├── 02_SOURCES/              ← Raw source material (immutable)
│   ├── 03_SOURCE_NOTES/         ← Processed extracts
│   ├── 04_CANON/                ← Synthesized knowledge (the wiki)
│   ├── 05_PROJECTS/             ← Project tracking
│   ├── 06_OUTPUTS/              ← Reusable deliverables
│   ├── 08_RESEARCH/             ← External topic knowledge
│   ├── 09_IDEAS/                ← Ideas pipeline
│   └── 10_META/                 ← System rules + templates
│
├── tools/                       ← 6 ingestion pipelines + 1 curation tool
│   ├── photo-processor/         ← iPhone photos → events, faces, locations
│   ├── takeout-processor/       ← Google Takeout → contacts, timeline
│   ├── chatgpt-ingest/          ← ChatGPT export → topic index
│   ├── facebook-ingest/         ← Facebook archive → message threads
│   ├── press-ingest/            ← Press URLs → cleaned local archive
│   ├── granola-ingest/          ← Granola meetings → rolling source-note
│   └── work-hero-picker/        ← Work folders → one canonical hero image each
│
├── README.md                    ← You are here
├── AGENTS.md                    ← Instructions for Codex
├── CLAUDE.md                    ← Instructions for Claude Code
├── .agents/skills/              ← Codex repo-scoped skills
├── RECIPES.md                   ← 24 step-by-step things to try
├── Standard Operating Procedure.md   ← Daily use, weekly maintenance, manual fallbacks
└── Data Sources to Gather.md    ← What raw materials to collect
```

---

## How it works

Material flows through layers, gaining structure at each step:

```
raw source → source note → canonical knowledge → project / output
```

Not every source becomes a note. Not every note becomes canon. The system is selective by design — fewer, better pages.

**Sources have trust levels.** When they disagree:
- **Journals** win for emotional truth and lived experience
- **Business documents** win for dates, amounts, and what actually happened
- **Press** tells you what others *think* happened — useful, but not ground truth
- **Your interviews** tell you what you chose to say publicly — performance, not diary

---

## AI skills

| Command | What it does |
|---------|-------------|
| `/ingest` | Process a raw source through the full vault pipeline |
| `/diarize` | Build a comprehensive page from all sources about a subject |
| `/enrich` | Fill out a thin page by finding all related sources |
| `/vault-lint` | Run 10 structural checks and write a report |
| `/improve` | Analyze patterns and propose system improvements |
| `/emerge` | Surface ideas the vault implies but never stated |
| `/challenge` | Pressure-test a belief against the vault's own evidence |
| `/connect` | Find hidden bridges between two topics |
| `/drift` | Compare stated priorities vs actual activity |
| `/ideas` | Vault-wide brainstorm grounded in what the vault knows |
| `/council` | 12 professional personas evaluate a project or idea |
| `/recap` | Close out a session with a dated "what changed / next / loose ends" entry |
| `/autoresearch` | Autonomous research loop on an external topic |
| `/granola` | Synthesize Granola meeting pulls (pairs with the `granola-ingest` tool) |
| `/voice` | Build (or refresh) a personal writing-voice skill from your own first-person sources |

You don't need to type the slash. Plain English works — *"build me a canon page about Devon"* runs the same path as `/diarize "Devon"`.

---

## Reference docs

- **`RECIPES.md`** — 24 step-by-step recipes (input → tool → skill → output) by data type. Open this first.
- **`Data Sources to Gather.md`** — What to collect and where each type goes
- **`Standard Operating Procedure.md`** — Daily use, weekly maintenance, manual fallbacks
- **`vault/10_META/AGENTS.md`** — The vault constitution: page types, naming conventions, source hierarchy, frontmatter schemas

### Codex-specific docs

- **`AGENTS.md`** — root-level Codex instructions for working from the repository root.
- **`vault/AGENTS.md`** — vault-level Codex instructions for sessions opened directly inside `vault/`.
- **`.agents/skills/creator-system-vault/SKILL.md`** — repo-scoped Codex skill that maps natural language requests and legacy `/command` names to the Creator System workflows.
- **`docs/CODEX.md`** — setup, usage, and validation notes for running this kit with Codex.

Run `bash scripts/check-codex-readiness.sh` after changing Codex instructions or skills.

---

## Without Claude Code

The system works entirely by hand. Open `vault/00_HOME/Start Here.md` in Obsidian and follow `Standard Operating Procedure.md`. Every workflow has a manual equivalent — AI just makes it faster.

---

## License

MIT — see [`LICENSE`](LICENSE). Attribution to Matty Mo Studio appreciated, not required.

---

> **Status:** Early version, currently in private beta with Cohort 01 of the Creator System cohort program. Active development. The kit is yours to use — the system is opinionated, but the data is always yours, on your laptop, in plain text.
