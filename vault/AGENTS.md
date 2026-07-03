# AGENTS.md

Vault-level instructions for Codex when the working directory is `vault/` or any child folder.

## Operating context

This folder is the user's Personal Intelligence System vault. It is designed to be opened in Obsidian and maintained by an agent. The full vault constitution lives at `10_META/AGENTS.md`; read it before making structural changes, creating new page types, or modifying workflows.

`CLAUDE.md` contains the original Claude Code onboarding behavior. For Codex, follow the same operating intent while using Codex-native capabilities and normal conversational instructions.

## First move in a session

1. Read `CLAUDE.md` to determine whether the vault is fresh or already personalized.
2. If placeholders such as `[Your Name]` are present, run the fresh-vault onboarding flow one step at a time.
3. If the vault is already personalized, orient from `00_HOME/Log.md`, then scan `01_INBOX/To Process/` for pending material before asking what the user wants to work on.

## Core rules

- Preserve the layer boundary: raw source, source note, canon, project, output.
- Never casually rewrite `02_SOURCES/`. Only file or format source material when the task explicitly requires it.
- Distinguish fact, inference, speculation, mythic language, and archival record.
- Prefer fewer, better pages over clutter.
- Add internal links when creating or updating pages.
- Log meaningful vault changes in `00_HOME/Log.md`.
- Use placeholders in examples; do not add real personal data to the public kit.

## Legacy command specs

The workflow specs live in `.claude/commands/`. Codex should treat them as reusable procedure documents, not as Claude-only files. When the user types or paraphrases one of these commands, read the corresponding file and execute that workflow:

- `/ingest` → `.claude/commands/ingest.md`
- `/diarize` → `.claude/commands/diarize.md`
- `/enrich` → `.claude/commands/enrich.md`
- `/vault-lint` → `.claude/commands/vault-lint.md`
- `/improve` → `.claude/commands/improve.md`
- `/emerge` → `.claude/commands/emerge.md`
- `/challenge` → `.claude/commands/challenge.md`
- `/connect` → `.claude/commands/connect.md`
- `/drift` → `.claude/commands/drift.md`
- `/ideas` → `.claude/commands/ideas.md`
- `/council` → `.claude/commands/council.md`
- `/recap` → `.claude/commands/recap.md`
- `/autoresearch` → `.claude/commands/autoresearch.md`
- `/granola` → `.claude/commands/granola.md`

## Validation from inside vault

From the repository root, run:

```bash
bash scripts/check-codex-readiness.sh
```

If working only from the vault folder, verify by inspection that this file, `../AGENTS.md`, and `../.agents/skills/creator-system-vault/SKILL.md` exist.
