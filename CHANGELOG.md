# Changelog

The format roughly follows [Keep a Changelog](https://keepachangelog.com). Versions are date-based (`YYYY-MM-DD`).

---

## [2026-07-03] — Codex support, work-hero-picker, `/voice` lands on main

### Added

- **Codex compatibility layer** — the kit now runs on OpenAI Codex as well as Claude Code:
  - `AGENTS.md` (repo root) and `vault/AGENTS.md` — Codex operating instructions mirroring `CLAUDE.md`
  - `.agents/skills/creator-system-vault/SKILL.md` — repo-scoped Codex skill mapping natural-language requests and `/command` names to the vault workflows
  - `docs/CODEX.md` — setup, usage, and validation notes
  - `scripts/check-codex-readiness.sh` + `.github/workflows/codex-readiness.yml` — CI check that the Codex layer stays consistent
- **`tools/work-hero-picker/`** — curation tool: generates a self-contained HTML picker for choosing one canonical "hero" image per work folder, with heuristic auto-ranking of candidates; applies selections as `_hero/` symlinks (originals never moved). Recipe 24 in `RECIPES.md`.

### Changed

- `/voice` (added 2026-05-24, contributed by Adam Mischke @vanities) merged to `main` and included in a packaged release for the first time — skill count is now 15.
- README, CLAUDE.md, and tools/README.md updated for the new counts (15 skills, 7 tools, 24 recipes).

---

## [2026-05-24] — `/voice` skill generator

### Added

- `/voice` command (`vault/.claude/commands/voice.md`) — generates a creator-specific writing-voice skill from the vault owner's own first-person sources in `02_SOURCES/`. Inventories surfaces, measures a quantitative fingerprint, extracts vocabulary + sentence patterns + verbatim calibration samples, generates anti-sample pairs, and emits `{slug}-voice/SKILL.md` symlinked to `~/.claude/skills/` for global invocation. Includes a refresh mode for incremental updates.
- `vault/10_META/Templates/Template - Voice Skill.md` — the schema `/voice` fills.

Contributed by Adam Mischke (@vanities).

---

## [2026-05-01] — Initial public release

First version distributed to Cohort 01 of the Creator System cohort program.

### Added

**Vault scaffolding**
- 10-folder layered structure (`00_HOME/` through `10_META/`)
- 14 AI skills in `vault/.claude/commands/` covering ingestion, synthesis, analysis, and maintenance
- Page-type templates in `10_META/Templates/` (Person, Project, Source Note, Decision, Output, Theme, Hub, Idea, Open Question, Project Framing Memo)
- Vault constitution at `10_META/AGENTS.md` — source hierarchy, naming conventions, frontmatter schemas, writing style
- Onboarding flow in repo-root `CLAUDE.md` — `let's go` triggers personalization, first ingest, first canon page, git init

**Ingestion tools** (`tools/`)
- 6 pipelines: `photo-processor`, `takeout-processor`, `chatgpt-ingest`, `facebook-ingest`, `press-ingest`, `granola-ingest`
- Shared utilities in `_shared/`
- README per tool with input format, run instructions, expected output

**Documentation**
- `README.md` — front-door overview with quick start
- `RECIPES.md` — 23 step-by-step recipes organized by data type
- `Standard Operating Procedure.md` — daily use, weekly maintenance, all workflows with manual fallbacks
- `Data Sources to Gather.md` — what raw materials to collect

**Internal release tooling** (for maintainers, not end users)
- `scripts/check-release.sh` — semantic block-list, empty-folders, wikilink resolution checks
- `scripts/package-release.sh` — deterministic zip builder with SHA256
- `scripts/prepare-repo.sh` — staging-and-audit tool
- `.github/workflows/release-check.yml` — CI runs the release check on every push

MIT `LICENSE`. Local-first. Plain text. Your data on your laptop.
