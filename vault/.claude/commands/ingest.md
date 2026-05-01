---
description: Process a raw source through the full vault pipeline — classify it, conditionally create a source note, update canon pages, and log the work. Use when new material arrives in the inbox or when pointing at a source file that has not been processed.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
origin: matty-mo-studio-creator-system/1.0
---

# Ingest

You are processing a raw source through this Personal Intelligence System's pipeline. Your job is to classify the source, decide whether a source note adds value, create it conditionally, update relevant canon pages, and log everything.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

---

## Non-negotiables

1. **Source Hierarchy is law.** Weight and trust evidence according to the hierarchy below. Never treat a press quote as fact without checking journals first.
2. **Source notes are conditional.** Not every source gets one. Follow the decision rules in Phase 3 exactly.
3. **Never modify files in `02_SOURCES/`** except to move an inbox item into its correct source location.
4. **Never silently upgrade speculative claims to canonical status** in an existing page. If a claim was speculative, it stays speculative unless a higher-trust source confirms it.
5. **Every ingest updates `00_HOME/Log.md`.** No exceptions.
6. **When updating existing canon pages, add — do not overwrite.** Only overwrite to correct a factual error, and cite the correcting source.
7. **Read `10_META/AGENTS.md`** before your first ingest in a session. It is the vault constitution. Follow its page type templates, frontmatter schemas, naming conventions, and writing style.

---

## Source Hierarchy

Every source in this vault has a trust level. When claims conflict between sources, the higher-trust source wins unless there is specific reason to doubt it.

```
L1  GROUND TRUTH      Journals (02_SOURCES/Personal/Journals/)
    First-person unfiltered accounts. What actually happened, when, with whom,
    and how it felt. Accept as factual unless internally contradicted.

L2  OPERATIONAL        File Vault docs (02_SOURCES/Business/File Vault/)
    Business documents, contracts, SOWs, financial records.
    Operational facts (dates, amounts, parties) are hard evidence.

L3  REFLECTIVE         Memoir (02_SOURCES/Personal/Memoir/)
    First-person but shaped for narrative. Dates and events are reliable.
    Emotional framing and causal claims are "narrator perspective."

L4  EXTERNAL           Articles (02_SOURCES/Practice/Articles/)
    Journalist-framed. May reflect editorial angle, simplification, or error.
    Verify facts against higher-trust sources when possible.

L5  PERFORMED          Transcripts (02_SOURCES/Practice/Transcripts/)
    The vault owner speaking publicly. May be intentionally myth-shaped, audience-calibrated,
    or strategically imprecise. Treat as "what they chose to say" not "what happened."

L6  PRIOR SYNTHESIS    Source notes (03_SOURCE_NOTES/) and canon pages (04_CANON/)
    Agent-generated synthesis. Reference but verify. May contain errors, omissions,
    or stale information.
```

---

## Phase 1: Locate and read the source

The user provides a file path, filename, or description of what to ingest.

### Step 1: Find the file

If the user gave a path, read it directly. If a filename, use Glob to find it. If a description, search `01_INBOX/` and `02_SOURCES/` for matches.

If no file is found, ask:

```
I cannot locate the source file.
Searched: [locations] for [terms].

a) Provide the exact file path
b) Paste the content directly so I can create the source file
c) Abort

Recommendation: A — the file may be named differently than expected.
```

### Step 2: Read the file completely

Read the entire source. Do not skim. Every detail matters for classification and extraction.

### Step 3: Classify the source

Determine all of the following:

- **Source type**: article, transcript, podcast, interview, journal_entry, memoir_manuscript, business_document, meeting_notes, document_archive, voice_note, other
- **Trust level**: L1 through L6 (see hierarchy above)
- **Date**: extract or infer the date of the source (not today's date)
- **Domain(s)**: Practice, Business, Personal, Shared, or combination
- **People mentioned**: list all by name
- **Projects mentioned**: list all by name
- **Places mentioned**: list all by name
- **Themes touched**: list all (use existing theme names from `04_CANON/Practice/Themes/` when they match)

---

## Phase 2: File the source

If the source is in `01_INBOX/`, move it to the correct permanent location:

| Source type | Destination |
|-------------|-------------|
| article | `02_SOURCES/Practice/Articles/` |
| transcript, podcast, interview | `02_SOURCES/Practice/Transcripts/` |
| journal_entry | `02_SOURCES/Personal/Journals/` |
| memoir_manuscript | `02_SOURCES/Personal/Memoir/` |
| business_document, meeting_notes, document_archive | `02_SOURCES/Business/Docs/` |

If the file is already in the correct `02_SOURCES/` location, skip this step.

Rename to match the vault naming convention if needed: `YYYY-MM-DD - Source - Short Title` (or `YYYY - Source - Short Title` if only the year is known).

---

## Phase 3: Decide whether to create a source note

This is a decision, not a default. Apply these rules:

**Create a source note when ANY of these are true:**
- The source has 3+ distinct people, themes, or insights worth cross-referencing
- The source will inform updates to 2+ canonical pages
- The source contains contradictions with existing vault knowledge
- The source is a primary source (journal, transcript) with quotable content worth preserving
- The source is part of a press cluster with no existing cluster note
- The source has template-worthy content (legal templates, SOW structures, operational playbooks)

**Skip the source note when ALL of these are true:**
- The source is a single-topic article that maps to one canon page update
- The insight can be captured in a sentence or two added directly to the relevant canon page
- No contradictions or notable nuance to preserve
- No quotable content worth extracting

If skipping, explain why in one sentence to the user, then proceed directly to Phase 4 (canon updates).

---

## Phase 3B: Write the source note

If creating a source note, write it to:

`03_SOURCE_NOTES/[year]/[YYYY-MM-DD - Note - Title].md`

Use the year of the source, not today's year, for the subfolder.

### Processing mode by source type

**Mode A: Journal entry (L1 — Ground Truth)**
- Treat every claim as fact unless internally contradicted.
- Extract: people, places, events, dates, emotional states, decisions, new information.
- Flag anything that contradicts existing canon — the journal wins.
- Always create a source note. Journals are primary sources with quotable, extractable content.

**Mode B: Press article (L4 — External)**
- Verify claims against higher-trust sources when possible (Grep journals and File Vault for the same events/dates).
- Check for a press cluster: use Grep to find other articles from the same week or event.
- If part of a cluster and a cluster note already exists, update that note instead of creating a new one.
- Note the journalist's angle. What framing choices did they make? What did they omit?

**Mode C: Interview transcript (L5 — Performed)**
- Flag statements that sound like public positioning rather than factual recounting.
- Mark quotes that appear rehearsed or repeated across transcripts (Grep for similar phrasing in other transcripts).
- Note audience context: who was the vault owner speaking to? Investors? Press? Fans? The audience shapes the performance.

**Mode D: Business document (L2 — Operational)**
- Operational facts (dates, amounts, parties, terms) are hard evidence.
- If the document is a single-purpose reference (template, checklist), skip the source note and file directly to `06_OUTPUTS/Templates/` if template-worthy.

**Mode E: Memoir manuscript (L3 — Reflective)**
- Separate "events" (dates, people, places — reliable) from "interpretations" (causal claims, emotional framing — narrator perspective).
- Always create a source note. Memoir is multi-topic and quotable.

**Mode F: Voice note or meeting notes**
- Extract actionable content. Apply the conditionality rules above.

### Source note template

```markdown
---
type: source_note
status: archival
source_type: [type]
date: YYYY-MM-DD
people:
  - [names]
projects:
  - [names]
places:
  - [names]
themes:
  - [theme_slugs]
---

# Note — [Title]

## What this is
[One paragraph: what the source is, who made it, when, format, trust level.]

Source: `[path to source file in 02_SOURCES/]`

## Summary
[2-3 sentences: what it says and why it matters to the vault.]

## Why it matters
[1-2 sentences: what this changes or enriches in vault knowledge.]

## Key facts
- [Bulleted facts extracted from the source. Cite trust level if mixing sources.]

## Key themes
- [Bulleted themes with brief annotation. Use existing theme names when they match.]

## Notable quotes
> [Direct quotes worth preserving, with speaker attribution]

## People mentioned
- [[Name]] — [role/context in this source]

## Projects mentioned
- [[Project]] — [how it appears in this source]

## Places mentioned
- [[Place]] — [context]

## Timeline implications
[What dates, sequences, or chronological claims does this source establish?]

## Contradictions / uncertainties
[Flag anything that conflicts with existing vault knowledge. Be specific about which sources disagree and at what trust level. If a journal says one thing and an article says another, note: "Journal (L1) says X. Article (L4) says Y. Journal takes precedence."]

## Pages to update
- [ ] [[Page]] — [what to add/change and from what trust level]

## Outputs this could fuel
[Potential downstream deliverables: bios, press language, essays, templates, decks.]
```

---

## Phase 4: Update canon pages

For each page listed in "Pages to update" (whether from the source note or identified directly):

### Step 1: Read the existing page

If the page exists, read it fully. Understand what is already there.

### Step 2: Determine where new information belongs

Match the new information to the page's existing section structure. If no appropriate section exists and the information is substantial enough to justify one, add a new section in the correct structural position.

### Step 3: Add the new content

- Cite the source: `(Source: [[source note name]])` or `(Source: journal, YYYY)`.
- If the new information contradicts existing content, do not delete the existing content. Add the new information alongside it with a note: "Note: [source] says X, while [other source] says Y."
- Match the writing style of the existing page.

### Step 4: Update frontmatter

- Set `last_updated` to today's date.
- Add any new `related_projects`, `related_places`, or `aliases` from the source.

### Step 5: Handle missing pages

If a page listed in "Pages to update" does not exist:
- Use Grep to check how many files link to that page name.
- If 3+ inbound links exist, create a thin page with the available information and correct frontmatter.
- If fewer than 3 inbound links, note it as a candidate for future creation but do not create it now.

---

## Phase 5: Log and navigate

### Step 1: Log the ingest

Append to `00_HOME/Log.md`:

```
## [YYYY-MM-DD] ingest | [Source short title]

- Source type: [type] | Trust: L[N]
- Source note: [created / skipped (reason)] [path if created]
- Canon updated: [[Page1]], [[Page2]], ...
- New pages created: [[Page]] (if any)
```

### Step 2: Update Index.md

If any new canon pages were created, add one-line entries to the appropriate section of `00_HOME/Index.md`.

---

## Phase 6: Suggest next actions

After completing the ingest, list:

- **Pages that need creation** — mentioned in the source but not yet existing, with inbound link counts
- **Contradictions that need resolution** — with the specific sources that disagree
- **Follow-up sources that would help** — "Ingesting the [specific source] would clarify [specific gap]"
- **Outputs that could be generated** — press kit language, essay topics, template extractions
- **Thin pages that could benefit from /enrich** — pages that exist but are stubs

---

## Escape hatches

- If the source file is empty or corrupt -> **BLOCKED.** "Source file is empty or unreadable."
- If you cannot determine the source type after reading it, present your best guess via AskUserQuestion. If still unclear after the user responds, file to `01_INBOX/To Process/` with a note and log as **NEEDS_CONTEXT.**
- If the source duplicates an already-ingested item (check `03_SOURCE_NOTES/` for existing notes on the same source) -> **DONE_WITH_CONCERNS.** Note the duplicate.
- If a canon page update would require substantial rewriting (more than adding a section) -> ask the user before proceeding. Suggest /enrich or /diarize instead.

---

## Completion

End with:

```
## Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
[one-line explanation if not DONE]
```
