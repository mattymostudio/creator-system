---
description: Take a thin or stub canon page and flesh it out by finding all available sources, applying the source hierarchy, filling missing sections, and adding cross-references. The inverse of diarize — starts from the page and works backward to sources. Use when a page exists but needs more depth.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit, WebSearch, WebFetch
origin: matty-mo-studio-creator-system/1.0
---

# Enrich

You are enriching an existing canon page in this Personal Intelligence System. Your job is to start from the page, find every source that mentions its subject, identify what is missing, and fill the gaps — without destroying what is already there.

This is the inverse of /diarize. Diarize builds from sources forward. Enrich starts from a page and works backward to sources.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

---

## Non-negotiables

1. **Source Hierarchy is law.** Weight evidence by trust level. See hierarchy below.
2. **Never delete existing content.** Only add, refine, or restructure. If existing content is wrong, add the correction alongside it with a note — do not silently replace.
3. **Every addition must cite its source.** Use `(Source: [[page name]])` notation.
4. **Preserve the page's existing voice and structure.** Match the writing style already present. Do not impose a different tone.
5. **If the page is already rich, say so.** Do not make changes for the sake of changes. A well-sourced, complete page does not need enrichment.

---

## Source Hierarchy

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

## Phase 1: Read and assess the target page

### Step 1: Find the target

The user provides a page name or path. Search `04_CANON/` first, then `05_PROJECTS/`, then all `.md` files. If multiple matches, present options via AskUserQuestion.

If no match is found, ask:

```
No page found matching "[subject]".

a) Provide the exact file path or name
b) Run /diarize instead to create a new page from scratch
c) Abort

Recommendation: B — if no page exists yet, /diarize is the right starting point.
```

### Step 2: Read the page completely

Record:
- Page type (from frontmatter `type` field)
- Current status
- All sections present (by heading)
- All sources currently cited
- All outbound wiki links
- All inbound wiki links (use Grep to find files that link to this page name)
- Line count (content only, excluding frontmatter)

### Step 3: Assess richness

A page is **thin** if any of these are true:
- Fewer than 15 lines of content (excluding frontmatter)
- Missing expected sections for its type (compare against templates in AGENTS.md)
- Fewer than 2 source citations
- Fewer than 3 outbound wiki links

A page is **rich** if:
- 50+ lines of content
- Multiple sections filled
- 3+ source citations
- 5+ outbound links

If the page is rich, ask:

```
This page is already well-developed.
[Name] has [N] lines, [N] source citations, and [N] outbound links.

a) Enrich anyway — search for sources that may have been missed
b) Focus on a specific section — tell me what to expand
c) Abort — the page is complete enough

Recommendation: [based on what you observe — if sources seem comprehensive, recommend C].
```

---

## Phase 2: Search for sources (read-only)

Extract the subject name and any aliases (from frontmatter `aliases` field or inline mentions in the page).

### Search systematically, in trust-level order

**L1 — Journals:** Grep `02_SOURCES/Personal/Journals/` for subject and aliases. Read surrounding context for each hit.

**L2 — File Vault:** Grep `02_SOURCES/Business/File Vault/` and `02_SOURCES/Business/Docs/`.

**L3 — Memoir:** Grep `02_SOURCES/Personal/Memoir/`.

**L4 — Articles:** Grep `02_SOURCES/Practice/Articles/`.

**L5 — Transcripts:** Grep `02_SOURCES/Practice/Transcripts/`.

**L6 — Source notes:** Grep `03_SOURCE_NOTES/`. Also check frontmatter `people`, `projects`, `places`, `themes` arrays in source notes for the subject name.

**L6 — Other canon:** Grep `04_CANON/`, `05_PROJECTS/`, `06_OUTPUTS/` for mentions of the subject in other pages.

**Web discovery (for gap-filling):** If the vault search reveals significant gaps (missing time periods, unknown relationships, or thin coverage), use WebSearch to find external sources that could fill them. Run 1-2 targeted searches. Record findings as:

```
WEB [source, URL]: [what this could add to the page]
```

Do not incorporate web findings into the page directly. Present them in the gap report (Phase 5) as sources the user could ingest.

### Compare findings to existing page content

For each source finding, check:
- Is this fact already on the page? -> skip
- Is this a new fact not yet captured? -> mark as addition
- Does this contradict something on the page? -> mark as contradiction
- Can this back-fill a source citation for an existing uncited claim? -> mark as citation

---

## Phase 3: Present the enrichment plan

Before writing anything, present a brief plan:

```
## Enrichment plan for [Name]

**New sources found:** [N] across [list of tiers with counts]
**New facts to add:** [count]
**Sections to fill or expand:** [list]
**Contradictions found:** [count — brief description of each]
**Source citations to add:** [count — existing claims that can now be backed]
**Cross-references to add:** [count]
**Estimated additions:** ~[N] lines

Proceed?
```

If the plan involves substantial changes (more than 20 new lines, any contradictions, or restructuring), wait for user confirmation.

For minor enrichments (a few facts, some links, source citations), proceed without asking.

---

## Phase 4: Write the enrichment

For each section of the page, working top to bottom:

### If the section exists and is adequate
Leave it alone. Do not rewrite good content.

### If the section exists but is thin
Add source-backed content below the existing content. Do not reorganize the existing text. Match its style. Add source citations.

### If a section is missing and should exist
Add it in the correct structural position (match the order used by rich pages of the same type in the vault). Use the templates from AGENTS.md as a guide.

### For every addition
- Cite the source: `(Source: [[source note or file name]])`
- Add confidence marker if the claim is substantive: `[journal-backed]`, `[press-only]`, `[cross-confirmed]`, etc.
- If the addition contradicts existing content, add a note: "Note: [[source]] says X, while the existing text says Y. [Source] is trust level L[N]."

### Update metadata
- Set `last_updated` to today's date
- Add any new `related_projects`, `related_places`, or `aliases` to frontmatter
- Add new wiki links to "Source notes" and "See also" sections

---

## Phase 5: Gap report

After enrichment, produce a "Still missing" assessment. Present it to the user (do not write it into the page):

```
## Still missing for [Name]

- [Specific gap 1] — no vault sources address this. Would need: [specific source type or document]
- [Specific gap 2] — partially addressed but needs: [what]
- [Specific gap 3] — single-source claim from [source]. Would benefit from: [cross-confirmation source]

Suggested next ingests:
- "[Specific source name or type]" would likely fill gaps [1] and [3]
- "[Specific source name or type]" would address gap [2]
```

If no gaps remain, say so: "No significant gaps identified. This page is now well-sourced."

---

## Phase 6: Log and navigate

### Step 1: Log

Append to `00_HOME/Log.md`:

```
## [YYYY-MM-DD] enrich | [Page Name]

- New sources found: [count]
- Lines added: ~[N]
- Sections filled: [list]
- Contradictions flagged: [count]
- Remaining gaps: [count]
```

### Step 2: Update Index.md

If the page was not already listed in `00_HOME/Index.md`, add it.

### Step 3: Suggest linking

If other pages mention this subject in their body text but do not wiki-link to this page, list the top candidates. Do not auto-edit other pages — present them to the user.

---

## Escape hatches

- If **no sources** mention the subject beyond what is already on the page -> **DONE.** "No new sources found. The page already captures what the vault contains about [subject]."
- If the target page **does not exist** -> ask whether to run /diarize instead.
- If enrichment would require **restructuring the entire page** (because the existing structure is fundamentally different from the vault templates) -> **NEEDS_CONTEXT.** "The current page structure differs from vault conventions. Should I restructure to match the [type] template, or add content within the existing structure?"
- If the page has **hand-written content** that would be displaced by enrichment -> ask before touching those sections. Hand-written content may reflect judgment that source material does not capture.

---

## Completion

End with:

```
## Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
[one-line explanation if not DONE]
```
