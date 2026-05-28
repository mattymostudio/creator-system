---
name: creator-system-vault
description: Use for Creator System vault work: onboarding, ingest, diarize, enrich, vault-lint, improve, emerge, challenge, connect, drift, ideas, council, recap, autoresearch, granola, source-note creation, canon updates, project pages, and Obsidian/markdown vault maintenance.
---

# Creator System Vault Skill

Use this skill when the user asks Codex to operate a Creator System vault, use a legacy slash command, process source material, build or update canon pages, maintain project pages, create reusable outputs, audit the vault, or reason from the user's archive.

## Read first

Before doing vault work, read these files as needed:

1. `AGENTS.md` at the repository root for repo-level expectations.
2. `vault/AGENTS.md` for vault-level Codex behavior.
3. `vault/10_META/AGENTS.md` for the full vault constitution.
4. `vault/CLAUDE.md` for onboarding state and fresh-vault behavior.
5. The relevant command spec in `vault/.claude/commands/` when a user invokes or paraphrases a workflow.

## Command mapping

Codex does not need Claude slash-command machinery. Treat these names as workflow aliases and execute the underlying markdown procedure:

| User request | Read this spec | Purpose |
|---|---|---|
| `/ingest` or process a source | `vault/.claude/commands/ingest.md` | Move raw material through classification, source note decisions, canon updates, and logging. |
| `/diarize` or build a comprehensive page | `vault/.claude/commands/diarize.md` | Synthesize all available material about a subject into a durable canon page. |
| `/enrich` or flesh out a thin page | `vault/.claude/commands/enrich.md` | Find related sources and improve an existing page with links and evidence. |
| `/vault-lint` or audit the vault | `vault/.claude/commands/vault-lint.md` | Check structure, links, duplicates, stale pages, and unresolved issues. |
| `/improve` or improve the system | `vault/.claude/commands/improve.md` | Analyze use patterns and propose practical system improvements. |
| `/emerge` or surface hidden ideas | `vault/.claude/commands/emerge.md` | Identify ideas implied by the archive but not yet explicitly stated. |
| `/challenge` or pressure-test a belief | `vault/.claude/commands/challenge.md` | Test a claim against the vault's own evidence. |
| `/connect` or find bridges | `vault/.claude/commands/connect.md` | Connect two topics, projects, people, or domains. |
| `/drift` or compare priorities vs activity | `vault/.claude/commands/drift.md` | Identify divergence between stated priorities and actual work. |
| `/ideas` or brainstorm from the vault | `vault/.claude/commands/ideas.md` | Generate grounded ideas from existing knowledge. |
| `/council` or convene advisors | `vault/.claude/commands/council.md` | Evaluate a project, idea, or decision from multiple expert perspectives. |
| `/recap` or close a session | `vault/.claude/commands/recap.md` | Write a dated session recap and next-step log. |
| `/autoresearch` or research a topic | `vault/.claude/commands/autoresearch.md` | Build external research notes under `08_RESEARCH/`. |
| `/granola` or synthesize meetings | `vault/.claude/commands/granola.md` | Process Granola meeting pulls into useful source notes. |

## Vault behavior

- Preserve raw sources. Do not overwrite `vault/02_SOURCES/` except for deliberate filing or explicit formatting tasks.
- Decide whether a source note is necessary before creating one. Not every source deserves a note.
- Update canonical pages cautiously. Add evidence, context, and links; do not silently overwrite prior synthesis.
- Distinguish canonical fact, working interpretation, speculation, mythic framing, and archival record.
- Use Obsidian-compatible markdown and stable noun-based page titles.
- Link related pages and update hubs when the work materially changes navigation.
- Log meaningful changes in `vault/00_HOME/Log.md`.

## Privacy and public-kit safety

This repository is public and should remain safe to ship. Use placeholder examples. Do not add real personal names, private source material, secrets, local machine paths, unpublished deal details, or private contact information.

## Finishing a task

A vault task is done when the requested output exists in the correct layer, relevant links are added, material uncertainty is visible, and meaningful changes are logged. For repo changes, run `bash scripts/check-codex-readiness.sh`; for release changes, also run `bash scripts/check-release.sh`.
