# Changelog

The format roughly follows [Keep a Changelog](https://keepachangelog.com). Versions are date-based (`YYYY-MM-DD`).

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
