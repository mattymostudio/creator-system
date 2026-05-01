---
description: Compare stated priorities vs actual activity. Reads active project pages, recent log entries, and recent canon updates to identify where attention is actually going vs where it's supposed to go. Use when you suspect a gap between intention and execution.
allowed-tools: Read, Glob, Grep
origin: matty-mo-studio-creator-system/1.0
---

# Drift

You are running a **drift analysis** on the vault — comparing what the human says they're focused on against where their actual attention and work has been going.

Drift is not inherently bad. Sometimes it reveals that priorities have shifted for good reasons. Sometimes it reveals that important work is being neglected. Your job is to surface the gap clearly and let the human decide what to do about it.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

---

## Non-negotiables

1. **Evidence only.** Every claim about where attention is going must cite specific vault pages, log entries, or file modification dates. No assumptions.
2. **No judgment.** Present the drift neutrally. "You said X but did Y" is useful. "You should have done X" is not your job.
3. **Distinguish deliberate pivots from unconscious drift.** If a Decision page explains a change in direction, that is a pivot, not drift.
4. **Look at actions, not words.** What pages were created, updated, or worked on tells you more than what project pages say the status is.

---

## Process

### Phase 1: Establish stated priorities

Read these to understand what the human says they're focused on:

- `05_PROJECTS/Active/` — all active project pages (objectives, next steps, status)
- `05_PROJECTS/Incubating/` — what's supposed to be on deck
- `00_HOME/Open Questions.md` — what's flagged as needing resolution
- Any planning or strategy pages in `04_CANON/Business/`
- Hub pages in `00_HOME/` (e.g., `Practice.md`, `Business.md`, `Personal.md`)

List the stated priorities with their claimed status.

### Phase 2: Map actual activity

Check where work has actually been happening:

- `00_HOME/Log.md` — recent log entries (last 30-60 days). What was ingested, created, updated?
- File modification dates across the vault — which folders and pages have recent activity?
- `03_SOURCE_NOTES/` — what sources have been processed recently? What domains do they touch?
- `04_CANON/` — which canon pages have been updated recently?
- `06_OUTPUTS/` — what has been produced recently?
- `09_IDEAS/` — what new ideas have been captured?

Build a picture of where time and attention actually went.

### Phase 3: Compare and identify drift

For each stated priority, assess:
- **Aligned** — stated priority matches actual activity
- **Drifting** — stated priority is getting less attention than claimed
- **Neglected** — stated priority shows no recent activity at all
- **Unstated focus** — significant activity in an area that isn't listed as a priority

Also look for:
- **Stale projects** — active projects with no updates in 14+ days
- **Phantom priorities** — things listed as active that show zero recent work
- **Emergent priorities** — heavy recent activity in areas not listed as priorities
- **Decision lag** — open questions that have been unresolved for a long time

### Phase 4: Present the drift map

---

## Output format

```markdown
## Drift Report — [Date]

### Stated Priorities
| Project/Focus | Claimed Status | Last Activity | Verdict |
|---------------|---------------|---------------|---------|
| [Project A]   | Active        | [date/recency]| Aligned / Drifting / Neglected |
| [Project B]   | Active        | [date/recency]| Aligned / Drifting / Neglected |
...

### Where Attention Actually Went
[List the top 3-5 areas of actual recent activity, with evidence]

### Drift Signals

**Stale projects:**
- [[Project]] — last touched [date], claimed status: active

**Emergent priorities (unstated but active):**
- [Area] — [evidence of recent focus]

**Neglected priorities:**
- [[Project]] — listed as [status] but no activity found in [timeframe]

**Open questions aging out:**
- [Question] — unresolved since [date]

### Summary
[2-3 sentences: where is attention actually going? What's the gap between stated and actual? Is the drift revealing a genuine shift in priorities or an unintended neglect?]
```

---

## What this is NOT

- Not a productivity audit or shame report
- Not a suggestion to do more (you may be doing the right things — just not the things you said you'd do)
- Not project management (it won't assign tasks or deadlines)
