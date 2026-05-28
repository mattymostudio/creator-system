# Using Creator System with Codex

Creator System now supports Codex alongside Claude Code. The goal is not to fork the product into two systems; it is to keep one vault architecture with two compatible agent entry points.

## What Codex reads

Codex discovers project instructions from `AGENTS.md` files in the repository hierarchy. This repo includes:

- `AGENTS.md` at the repository root for project-wide guidance.
- `vault/AGENTS.md` for sessions opened directly inside the Obsidian vault.
- `.agents/skills/creator-system-vault/SKILL.md` as a repo-scoped skill for vault operations.

The existing Claude Code files remain in place:

- `CLAUDE.md`
- `vault/CLAUDE.md`
- `vault/.claude/commands/*.md`

Codex should treat the command markdown files as workflow specs. For example, when a user asks for `/ingest`, Codex should read `vault/.claude/commands/ingest.md` and execute the workflow in normal Codex mode.

## Local Codex setup

1. Clone the repo.

```bash
git clone https://github.com/mattymostudio/creator-system.git
cd creator-system
```

2. Open the repo with Codex. Starting at the repository root is recommended because Codex will load `AGENTS.md` and discover `.agents/skills/`.

3. Ask Codex to summarize active instructions. It should mention the root `AGENTS.md`, the vault instructions, and the Creator System vault skill.

4. Open the same folder in Obsidian if you want to see files change live.

## Codex cloud setup

Use the repo root as the working directory. The project has no required install step for vault-only workflows. If you plan to modify or run ingestion tools under `tools/`, configure the Codex environment with the appropriate Python dependencies for that tool.

Suggested validation command:

```bash
bash scripts/check-codex-readiness.sh
```

For release branches, also run:

```bash
bash scripts/check-release.sh
```

## How to prompt Codex

Start with natural language. These are equivalent intents:

```text
let's go
process the file I put in the inbox
/ingest the latest meeting transcript
build a canon page about this project
/diarize Project - Example
run a vault lint and tell me what to fix first
```

Codex should map those requests to the repo skill and, when needed, the legacy command specs.

## Compatibility rule

When updating workflows, keep Claude Code and Codex behavior aligned. If a process changes in `vault/.claude/commands/`, update `.agents/skills/creator-system-vault/SKILL.md` or `vault/AGENTS.md` if Codex needs new routing instructions. If Codex guidance changes the behavior of a workflow, update the relevant Claude command spec too.

## Validation checklist

A Codex-ready branch should satisfy:

- Root `AGENTS.md` exists and is under the default project-document budget.
- `vault/AGENTS.md` exists for vault-level sessions.
- `.agents/skills/creator-system-vault/SKILL.md` has valid frontmatter with `name` and `description`.
- README mentions Codex as a supported agent surface.
- Legacy Claude command specs are still present.
- Public release checks still pass.
