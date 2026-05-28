# AGENTS.md

Repository-level instructions for Codex working on Creator System.

## What this repository is

Creator System is a local-first Personal Intelligence System for creative professionals. It is an Obsidian-compatible vault scaffold plus ingestion tools and agent workflows that help a user turn source material into structured notes, canonical knowledge, project pages, and reusable outputs.

The repository supports two agent surfaces:

- Claude Code reads `CLAUDE.md` and `vault/.claude/commands/`.
- Codex reads this file, `vault/AGENTS.md`, and repo skills under `.agents/skills/`.

Do not remove Claude Code support while adding Codex support. The two surfaces should stay behaviorally aligned.

## Important paths

- `vault/` — the user-facing knowledge system and Obsidian vault.
- `vault/10_META/AGENTS.md` — the full vault constitution: source hierarchy, page types, frontmatter guidance, naming conventions, workflows, and conduct rules.
- `vault/.claude/commands/` — canonical workflow specs for the existing skills. Codex should read these when a user invokes a legacy slash command such as `/ingest` or `/diarize`.
- `.agents/skills/creator-system-vault/SKILL.md` — Codex skill that maps Creator System workflows into Codex-native behavior.
- `tools/` — ingestion pipelines.
- `scripts/` — release and validation scripts.
- `docs/CODEX.md` — human-readable Codex setup and usage guide.

## How to work in this repo

1. Orient before editing. Read `README.md`, this file, and the most relevant deeper instructions. For vault behavior, read `vault/AGENTS.md` and `vault/10_META/AGENTS.md`.
2. Preserve the existing source hierarchy: raw source, source note, canon, project, output. Do not collapse these layers.
3. Preserve privacy defaults. Do not add personal examples, private names, local paths, sample secrets, or real user source material. Use placeholders.
4. Maintain compatibility with plain-text Obsidian markdown. Prefer simple files over hidden state, databases, or external services.
5. Keep agent guidance concise and practical. Codex has a default project-document budget, so prefer links to detailed docs over copying long sections everywhere.
6. When behavior changes, update the relevant human docs and the relevant agent instructions together.

## Codex operating rules

When a user opens Codex at the repository root:

- Treat `vault/` as the working vault unless the user explicitly asks to work on tools, scripts, or release packaging.
- For Creator System operations, use the repo skill in `.agents/skills/creator-system-vault/SKILL.md`.
- If the user invokes a legacy slash command, read the corresponding markdown spec in `vault/.claude/commands/` and execute the workflow in normal Codex prose.
- If the user asks to onboard a fresh vault, follow the onboarding behavior described in `CLAUDE.md` and `vault/CLAUDE.md`, but translate any Claude-specific wording into agent-neutral language.
- If the user asks for a durable artifact, save it in the correct vault layer and update links/logs when appropriate.

## Validation

Run the narrowest check that matches the change:

```bash
bash scripts/check-codex-readiness.sh
```

For public release or broad repo changes, also run:

```bash
bash scripts/check-release.sh
```

If a script cannot run because the local checkout is partial, missing dependencies, or outside a full git repository, state that clearly and validate by inspection where possible.

## Done means

A change is complete when:

- Codex can discover root instructions from `AGENTS.md`.
- Codex sessions opened inside `vault/` can discover `vault/AGENTS.md`.
- The repo skill has valid `SKILL.md` frontmatter and points Codex to the existing workflow specs.
- Human docs explain how to use either Claude Code or Codex.
- Release checks still pass or any failures are explicitly explained.
