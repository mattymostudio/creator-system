---
name: granola-ingest-pull
description: Stage 1 of the Granola ingest. Pull new meetings via MCP since the last archive's cutoff, dump raw JSON + manifest to tools/_outputs/granola/. Does not touch the vault.
---

# Granola ingest — Stage 1: pull

Working directory: `/path/to/creator-system`

You are the pull half of the Granola ingest. Your job is to discover new meetings since the last vault archive's high-water mark and dump them to a JSON file for the vault synthesis step.

## Non-negotiables

1. **Do not modify the vault** in this stage. No writes to `vault/`.
2. **Do not call `git`** — this workspace is not a git repo.
3. **Dedupe by date** — never pull meetings already covered by the latest archive.
4. **Fail loud on MCP errors** — if `mcp__granola__*` tools don't resolve, stop and tell the user to check the Granola MCP connection. Do not invent data.

## Steps

### 1. Find the high-water mark

```
ls vault/03_SOURCE_NOTES/2026/ | grep "Granola Meeting Archive"
```

Pick the file whose title date range ends latest. Read it and extract:

- **Title end date** — e.g. `(Feb 2026 - Apr 2026)` → Apr 15, 2026 (confirmed by body header "Feb 19, 2026 -- Apr 15, 2026").
- **Updated line in body** — e.g. `Source: Granola MCP integration, pulled 2026-04-14. Updated 2026-04-16 (+4 meetings).`

High-water mark = the **later** of (title end date, latest Updated date). This is the day we pulled through; start the new window from the day after.

If no archive exists at all, fall back to 30 days ago and flag it in the manifest.

### 2. List new meetings

Call `mcp__granola__list_meetings` with:
- `time_range: "custom"`
- `custom_start`: `<high-water + 1 day>T00:00:00`
- `custom_end`: `<today>T23:59:59`

If count is 0: write a one-line "no new meetings" manifest and stop. Do not write an empty JSON dump.

### 3. Fetch summaries

Batch meeting IDs into groups of 10. For each batch, call `mcp__granola__get_meetings` with the IDs.

For each meeting, capture:
- `id`
- `title`
- `date` (ISO)
- `participants` (names + emails if present)
- `summary` (AI summary)
- `notes` (private notes if present)
- `signal`: `"normal"` or `"low"` — mark `"low"` if summary empty / "No summary" / under ~200 chars

### 4. Write the JSON dump

Path: `tools/_outputs/granola/<YYYY-MM-DD>-pull.json`

Schema:
```json
{
  "pulled_at": "<ISO-8601 timestamp, local TZ>",
  "window_start": "<YYYY-MM-DD>",
  "window_end": "<YYYY-MM-DD>",
  "last_archive_file": "<basename of the archive file you read>",
  "high_water_source": "title-date | updated-line",
  "meetings": [
    {
      "id": "...",
      "title": "...",
      "date": "...",
      "participants": [{"name": "...", "email": "..."}],
      "summary": "...",
      "notes": "...",
      "signal": "normal"
    }
  ]
}
```

If a file already exists at that path (same-day re-run), append `-v2`, `-v3` etc. before `.json` — never silently overwrite.

### 5. Write the manifest

Path: `tools/_outputs/granola/<YYYY-MM-DD>-manifest.md`

Format:
```markdown
# Granola pull — <YYYY-MM-DD>

- **Window:** <start> → <end>
- **Last archive:** <filename>
- **Count:** <N total> (<N normal>, <N low-signal>)
- **JSON:** <path>

## Meetings

| Date | Title | Participants | Signal |
|---|---|---|---|
| 2026-04-15 | ... | Jane D, Collaborator Two | normal |
| 2026-04-17 | ... | Jane D | low |

## Next step

In a vault session, run:
`/granola tools/_outputs/granola/<YYYY-MM-DD>-pull.json`
```

### 6. RECAP

Write `tools/granola-ingest/.claude/RECAP.md` (overwrite, not append — see workspace recap convention):

```markdown
# Granola ingest — RECAP

**Last run:** <ISO>
**Window:** <start> → <end>
**Pulled:** <N> meetings (<N normal>, <N low-signal>)
**Dump:** tools/_outputs/granola/<date>-pull.json
**Status:** pending synthesis / synthesized / stopped (reason)

## What's next
- Run `/granola <dump-path>` in a vault session to synthesize

## Loose ends
- <anything to flag>
```

### 7. Report to user

End with a short summary: window, count, dump path, and the exact `/granola <path>` command to run next.

## Dry-run mode

If the user says "dry run" or "smoke test": do steps 1-3, report count + titles + rough signal distribution, **skip** writes in steps 4-6.
