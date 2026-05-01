---
description: The vault learning loop. Reads the lint report, recent log entries, and structural patterns, then proposes specific improvements to AGENTS.md rules, templates, or skill files. Use when you want to evolve the vault's operating system based on what has been learned.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
origin: matty-mo-studio-creator-system/1.0
---

# Improve

You are running the vault's learning loop. Your job is to analyze health signals — the lint report, the log, the current AGENTS.md rules, and actual vault practice — then propose specific, concrete improvements to the vault's meta layer.

This is not a cleanup tool. Vault-lint catches structural issues. /improve catches systemic patterns and evolves the rules.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

---

## Non-negotiables

1. **Never write changes without explicit user approval for each proposal.** Present every change, wait for yes/no/modify per proposal.
2. **Proposals must include before/after.** Show what the rule says now and what it would say after the change.
3. **Focus on patterns, not individual files.** A single broken link is a lint issue. 55 broken links with the same root cause is an /improve issue.
4. **Prioritize prevention over remediation.** Changes that prevent future problems are more valuable than changes that fix current ones.
5. **AGENTS.md should get sharper, not longer.** Do not add complexity without clear payoff. If a rule can be simplified, simplify it.

---

## What NOT to do

- Do not propose new page types unless 3+ files clearly need a type that does not exist.
- Do not propose frontmatter fields no one will use or query.
- Do not suggest reorganizing the folder structure unless a structural problem is causing real operational friction (not theoretical elegance).
- Do not "fix" things that are working. If practice diverges from rules but the practice is better, propose changing the rule to match practice.
- Do not propose changes that only affect aesthetics or formatting.

---

## Phase 1: Collect signals (read-only)

### Step 1: Read the lint report

Read `10_META/Vault Lint Report.md`. If it does not exist, tell the user:

```
No lint report found. Run /vault-lint first to generate baseline data, then run /improve again.
```

Extract from the lint report:
- Counts per check and severity
- Patterns in the findings (not individual violations — recurring root causes)
- The Top 5 Recommendations section

### Step 2: Read recent log entries

Read `00_HOME/Log.md`. Focus on the 10-15 most recent entries. Extract:
- What types of work have been happening (ingests, diarizations, enrichments, structural changes)
- What problems were encountered and how they were resolved
- Patterns in what is being created (mostly people pages? mostly source notes? mostly outputs?)

### Step 3: Read Open Questions

Read `00_HOME/Open Questions.md`. Identify:
- Questions that suggest missing rules or templates
- Questions that were resolved — their resolution may imply a pattern worth encoding

### Step 4: Read AGENTS.md

Read `10_META/AGENTS.md` fully. Note:
- Rules that are unclear or ambiguous
- Rules that are contradicted by actual vault practice (compare naming conventions in AGENTS.md against actual filenames using Glob)
- Missing guidance that the log entries suggest was needed
- Sections that have grown stale or verbose

### Step 5: Read skill files

Read all files in `.claude/commands/`. Check for:
- Inconsistencies between skill instructions and AGENTS.md rules
- Missing skill coverage (common operations that should be skills but are not)
- Skill instructions that the log suggests were inadequate

### Step 6: Spot-check recent files

Use Glob to find the 10 most recently modified `.md` files (by git timestamp or file metadata). Read each one. Assess:
- Do they follow AGENTS.md rules?
- Do they use correct frontmatter?
- Do they follow naming conventions?
- If they diverge, is the divergence better than what the rules specify?

---

## Phase 2: Analyze

Categorize all findings into four buckets:

### A: Rule fixes

Places where AGENTS.md says one thing but the vault does another, and the vault's practice is correct.

Example: AGENTS.md says `Project - Name` but all project files use `Project - Name`. The rule should be updated to match practice.

### B: Template gaps

Page types, sections, or patterns that keep being needed but are not defined.

Example: If multiple source notes use a "Press cluster" pattern not described in AGENTS.md, propose adding `press_cluster` as a recognized source_type.

### C: Workflow improvements

Changes to ingest, lint, or synthesis workflows that would prevent recurring issues.

Example: If the lint report shows many broken links to ingest notes, propose a rule that ingest notes must use specific, unique titles rather than generic ones.

### D: Skill improvements

Specific changes to skill files based on operational evidence.

Example: If the log shows that /ingest was run on a press article and the user had to manually decide to cluster it, propose adding explicit press cluster detection to the /ingest skill.

---

## Phase 3: Propose changes

Present each proposal individually. Use this format:

```
---

### Proposal [N]: [Short descriptive title]

**Category:** Rule fix | Template gap | Workflow improvement | Skill improvement
**Target file:** [exact file path to modify]

**Evidence:**
[What data led to this proposal — specific counts, log entries, lint findings, file examples.]

**Current state:**
[What the target file currently says. Quote the exact text. Or "not addressed" if the guidance is missing.]

**Proposed change:**
[Exactly what to change. Show the new text that would replace or augment the current text.]

**Impact:**
[What this prevents, enables, or improves. Be specific.]

**Risk:**
[What could go wrong. If low risk, say "Low — this aligns practice with existing convention."]

**Approve? (y / n / modify)**
```

Present proposals in priority order: highest-impact first.

If you have more than 7 proposals, present the top 7 and note how many more exist. Ask the user if they want to see the rest.

---

## Phase 4: Implement approved changes

For each proposal the user approves:

### Step 1: Make the change

Edit the target file with the exact change proposed. Use the Edit tool — do not rewrite entire files.

### Step 2: Note cascading effects

If the change affects naming conventions: count how many existing files would need renaming, but do NOT rename them in this run. Note the count for the user.

If the change affects frontmatter schemas: count how many existing files would need updating, but do NOT update them in this run. Note the count.

If the change affects skill behavior: note which skills are affected and what would change about their operation.

### Step 3: Verify the edit

Read back the edited section to confirm the change was applied correctly.

---

## Phase 5: Log

Append to `00_HOME/Log.md`:

```
## [YYYY-MM-DD] improve | [summary]

Proposals reviewed: [total count]
Approved: [count]
Changes made:
- [Proposal N]: [one-line summary of what changed in what file]
- [Proposal M]: [one-line summary]
Cascading effects noted:
- [N] files would need [type of update] — not done in this run
```

---

## Phase 6: Suggest next run

After completing, suggest what the user should do next:

- If cascading file updates are needed: "Consider running /vault-lint to assess the current state, then address the [N] files that need [update type]."
- If new patterns emerged during analysis: "I noticed [pattern] that might warrant a follow-up /improve run after more data accumulates."
- If skills were changed: "The changes to [skill] will take effect on the next invocation. Consider testing with a real item."

---

## Escape hatches

- If **no lint report exists** -> tell the user to run /vault-lint first. **NEEDS_CONTEXT.**
- If the lint report and log show **no patterns worth addressing** -> **DONE.** "Vault operating system is consistent with practice. No changes proposed. The rules match what the vault is actually doing."
- If proposed changes **conflict with each other** -> present the conflict explicitly and ask the user to choose.
- If a proposed change would affect **more than 50 files** downstream -> flag it as a major change and recommend a phased approach rather than a single rule update.

---

## Completion

End with:

```
## Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
[one-line explanation if not DONE]
```
