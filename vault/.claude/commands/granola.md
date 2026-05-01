---
description: Stage 2 of the Granola ingest. Read a Granola pull JSON and synthesize it into the rolling thematic Granola Meeting Archive note. Extends the current archive or opens a new one when a window rolls over.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
argument-hint: <path to granola pull JSON (typically tools/_outputs/granola/YYYY-MM-DD-pull.json)>
origin: matty-mo-studio-creator-system/1.0
---

# /granola — Synthesize Granola pull into the archive

You are the synthesis half of the Granola ingest. The pull step (from the `granola-ingest` tool in the Ingestion Tools pack) already wrote a JSON dump containing new meetings since the last archive's high-water mark. Your job is to turn those into additions to the rolling thematic archive in `03_SOURCE_NOTES/`.

**Working directory:** vault root.
**Input:** path to the pull JSON passed as `$ARGUMENTS`. If missing, search for the newest `*-pull.json` under the companion Ingestion Tools output dir (ask the user to confirm the path before proceeding).

---

## Non-negotiables

1. **Follow vault rules.** Read `10_META/AGENTS.md` if unsure about page type templates, frontmatter schemas, or writing style.
2. **Never modify `02_SOURCES/`.** The pull JSON is the source of record; do not copy meeting content into `02_SOURCES/`.
3. **Source notes live in `03_SOURCE_NOTES/<year>/`.**
4. **Add, don't overwrite.** When extending the current archive, append new sections and merge frontmatter arrays — never rewrite existing theme sections.
5. **Don't touch `04_CANON/`.** Canon maintenance is a separate pass handled by `/enrich` and `/vault-lint`. This command only *flags* needed updates in the archive's "Pages to update" section.
6. **Distinguish fact from interpretation.** Label speculative claims as such. Do not upgrade a speculation found in a meeting summary to a canonical claim.
7. **Always log to `00_HOME/Log.md`** at the end.

---

## Phase 1: Read the pull

1. Resolve the pull path from `$ARGUMENTS`. If the path is relative, resolve against the vault root or the companion `tools/` location.
2. Read the JSON. Pull: `window_start`, `window_end`, `last_archive_file`, `meetings[]`.
3. If `meetings[]` is empty, stop — tell the user the pull is empty.
4. Separate `meetings[]` into:
   - `normal` signal — full synthesis candidates
   - `low` signal — listed in a compact "Also this window" roll-up, not synthesized
5. Also flag any meeting that *looks* low-signal but was marked `normal` (e.g. solo meetings with no participants + thin summary) so you can downgrade it.

## Phase 2: Decide append vs new archive

Read the archive named in `last_archive_file`. Look at its title date range.

**Rules:**
- If `window_end` falls within **~2 months of the archive's start date**: **append** to the current archive. (Typical cadence is 2-3 month windows per archive file.)
- If `window_end` pushes the total span beyond ~3 months from the archive's start: **open a new archive** with filename `<YEAR> - Note - Granola Meeting Archive (<OldEnd-Month> <YEAR> - <NewEnd-Month> <YEAR>).md`. The *previous* archive's end should match the previous `Updated` high-water — leave it as-is.
- If the current archive doesn't exist (first run ever): create the first archive.

If you're uncertain, show the user your choice with the filename you'd use and ask before writing.

## Phase 3: Synthesize the new content

For each **normal**-signal meeting:

1. Extract:
   - Key facts (decisions, numbers, commitments, dates)
   - People named (full names where possible; note spelling uncertainties as `[[Person?]]`)
   - Projects named
   - Themes touched
   - Next steps / open questions
   - Contradictions with prior archive content (if any)

2. **Group by theme / project, NOT by meeting.** This is the core editorial move. Match the existing archive's structure — look at section headings in `last_archive_file` and reuse them when relevant. Create new section headings only when a genuinely new theme emerges.

3. **Writing style:**
   - High-signal bullets, not prose paragraphs
   - Numbers/dates/names inline, not in footnotes
   - Wikilinks on first mention of a person or project: `[[Name]]`
   - Label speculative claims: `speculative:` or `possibly:` prefix
   - No filler. No "the conversation explored…" — just what was decided or said.

4. **For low-signal meetings**, add a single-line entry to the "Also this window" roll-up: `YYYY-MM-DD — <title> — <one-line gist if any> — [low-signal]`.

## Phase 4: Update frontmatter

Merge new entries into the archive's YAML arrays (de-duped, preserving existing order + appending new):
- `people:` — union of existing + new names
- `projects:` — union
- `themes:` — union

Leave `type`, `status`, `source_type`, `date` (today, if this is the first write of the session) unchanged or set if missing.

## Phase 5: Update the Source + Tracking sections

1. **Update the `Source:` line** at the top of the body:

   `**Source:** Granola MCP integration, pulled <pulled_at>. Updated <today> (+<N> meetings).`

   If an `Updated` line already exists with a prior date, chain additional updates.

2. **Extend "People, Projects & Themes to Track"** — add new `[[Entity]]` bullets for anything new this window. Use the same phrasing pattern as existing entries (wikilink + short hyphenated annotation of what's relevant).

3. **Extend "Open Questions"** — add any questions raised by this window's meetings that aren't resolvable from the JSON.

4. **Add a "Pages to update" subsection** under "People, Projects & Themes to Track" (if not already present) listing canon pages that should be enriched or created in a later `/enrich` pass:
   ```
   ## Pages to update (for next /enrich pass)
   - [[Person Name]] — new page needed (<role, relevance>)
   - [[Project Name]] — add: <specific context from this window>
   ```

## Phase 6: Log

Append to `00_HOME/Log.md`:

```markdown
## <YYYY-MM-DD> — Granola ingest

Pulled <N> meetings (<start> → <end>) via Granola MCP. Synthesized into [[<archive filename without .md>]] (+<N normal>, <N low-signal>). New entities flagged: <short list>. Pull dump: `<path to JSON>`.
```

## Phase 7: Report

End with a short summary:
- Archive file touched (append / new)
- Meetings synthesized vs low-signal-rolled-up
- New entities flagged for canon (counts)
- Any open questions or flagged contradictions
- Suggest `/enrich` on top 2-3 canon pages if multiple updates accumulated

---

## Edge cases

- **Same meeting appears twice** (participant name variant, rerun): dedupe by `id` inside the JSON, and also check the archive body for a meeting-specific sentence you already wrote. Do not double-write.
- **Low-signal only**: if every meeting is low-signal, still update the "Also this window" roll-up, frontmatter, and Source line, and log. Don't add empty theme sections.
- **Pull JSON missing fields**: if `summary` is missing, treat as low-signal regardless of the pull's own `signal` flag.
- **Contradiction with prior archive**: add a line in-section with `contradicts earlier claim that <X>` and surface it in "Open Questions". Do not silently rewrite the earlier claim.

---

## Dry-run mode

If the user says "dry run" or "show me what you'd write": do Phases 1-3, report the proposed section edits and frontmatter additions as a diff preview, **do not** write to the archive or log.

---

## Requires

This command depends on the `granola-ingest` tool from the companion Ingestion Tools pack, which produces the pull JSON and (optionally) syncs with Granola via MCP. Without it, you can still use `/granola` by handing it any structured JSON that matches the expected schema (`window_start`, `window_end`, `last_archive_file`, `meetings[]`).
