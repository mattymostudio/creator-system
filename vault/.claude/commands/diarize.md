---
description: Read all sources about a person, place, entity, or concept across the vault and produce a structured diarization — a single authoritative page distilled from many documents. Use when you want a comprehensive canon page built from scratch by reading everything available about a subject.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit, WebSearch, WebFetch
origin: matty-mo-studio-creator-system/1.0
---

# Diarize

You are producing a structured diarization for a single subject in this Personal Intelligence System. Your job is to read every source that mentions this subject, synthesize them according to the source hierarchy, and write a rich canon page with explicit provenance, confidence markers, and gap analysis.

A diarization is not a summary. It is a page of judgment distilled from dozens of documents — the model equivalent of an analyst's brief.

**Working directory:** The vault root (the directory containing 00_HOME through 10_META).

---

## Non-negotiables

1. **Source Hierarchy is law.** Every factual claim must be weighted by its source trust level. When sources conflict, the higher-trust source wins.
2. **Every claim cites its source.** Use parenthetical `(Source: [[page name]])` notation. No uncited claims.
3. **Contradictions are preserved, never flattened.** If journals say one thing and press says another, both appear with labels and trust levels.
4. **Confidence markers on substantive claims:** `[journal-backed]`, `[press-only]`, `[transcript-only]`, `[single-source]`, `[cross-confirmed]`.
5. **Never overwrite an existing rich page without asking.** If a canon page already exists with substantial content, ask before replacing.
6. **Follow AGENTS.md.** Read `10_META/AGENTS.md` for page type templates, frontmatter schemas, naming conventions, and writing style.

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

L5b DISCOVERED         Web search results (found via WebSearch during diarization)
    External sources not yet in the vault. Useful for discovering coverage, context,
    and facts not captured internally. Treat as L4 quality (journalist-framed) but
    flag as "not yet ingested" — the user should decide whether to ingest them.

L6  PRIOR SYNTHESIS    Source notes (03_SOURCE_NOTES/) and canon pages (04_CANON/)
    Agent-generated synthesis. Reference but verify. May contain errors, omissions,
    or stale information.
```

---

## Phase 1: Identify the subject

The user provides a subject name. Determine the subject type:

- If the subject matches a person name or alias -> type is `person`
- If the subject matches a place name -> type is `place`
- If the subject matches a company, project, or organization -> type is `entity`
- If the subject is a concept, theme, or abstract noun -> type is `theme`

If the type is ambiguous, ask:

```
What type of page should this be?

The subject "[name]" could be classified multiple ways.

a) Person — an individual human being
b) Entity — a company, organization, or project
c) Place — a geographic location
d) Theme — a concept or recurring idea

Recommendation: [your best guess] because [one-line reason].
```

### Check for existing page

Use Glob to search for a file matching the subject name in `04_CANON/`. If found, read it and assess:

- If the page has **fewer than 15 lines of content** (excluding frontmatter): proceed with diarization. The existing page is a stub.
- If the page has **15-50 lines**: ask the user:

```
A page exists for [subject] with [N] lines of content, last updated [date].

a) Overwrite — replace with a fresh diarization from all sources
b) Merge — add new findings while preserving existing content
c) Abort

Recommendation: [merge if existing content looks hand-written or high-quality; overwrite if it looks thin or auto-generated].
```

- If the page has **more than 50 lines**: ask the user before proceeding. Suggest /enrich instead if the goal is incremental improvement.

---

## Phase 2: Collect all sources (read-only)

Search the entire vault AND the web for every mention of the subject. Use the subject's name and any known aliases. For each search, read the surrounding context — not just the matching line.

### Step 0: Web discovery (L5b — external sources not yet in vault)

Before searching the vault, use WebSearch to discover external sources about the subject. Run 1-3 searches:

- `"[subject name]" "[vault owner or practice name]"` — find coverage connected to the practice
- `"[subject name]" [relevant context keywords]` — broader discovery
- If the subject is a person: `"[subject name]" [their field or company]`

For each relevant result, use WebFetch to read the page content. Record findings as:

```
WEB [source, URL]: [key facts or claims found]
```

**Do NOT incorporate web findings directly into the diarization at the same trust level as vault sources.** Web results are discovery — they tell you what exists out there. At the end of the diarization, present web findings separately as:

```
## Sources discovered (not yet in vault)

- [Title] — [URL] — [one-line summary of what this adds]
  Recommendation: [ingest / skip / already captured in vault]
```

The user decides whether to ingest these. If they say yes, suggest running /ingest on each one.

### Step 1: Search journals (L1)

Use Grep to find every mention in `02_SOURCES/Personal/Journals/`. For each hit, read the full surrounding entry. Record findings as:

```
JOURNAL [year]: [factual claim or observation]
```

### Step 2: Search File Vault docs (L2)

Use Grep to search `02_SOURCES/Business/File Vault/` and `02_SOURCES/Business/Docs/`. Record as:

```
FILE_VAULT [doc name]: [operational fact]
```

### Step 3: Search memoir (L3)

Use Grep to search `02_SOURCES/Personal/Memoir/`. Record as:

```
MEMOIR: [passage summary, separating events from interpretations]
```

### Step 4: Search articles (L4)

Use Grep to search `02_SOURCES/Practice/Articles/`. Record as:

```
ARTICLE [publication, date]: [claim, noting journalist framing]
```

### Step 5: Search transcripts (L5)

Use Grep to search `02_SOURCES/Practice/Transcripts/`. Record as:

```
TRANSCRIPT [source, date]: [what the vault owner said, noting audience context]
```

### Step 6: Search source notes (L6)

Use Grep to search `03_SOURCE_NOTES/`. Read each matching note fully. Record as:

```
SOURCE_NOTE [note title]: [relevant synthesis]
```

### Step 7: Search existing canon and project pages (L6)

Use Grep to search `04_CANON/`, `05_PROJECTS/`, and `06_OUTPUTS/`. Record as:

```
CANON [page]: [relevant content]
```

---

## Phase 3: Analyze (no writes yet)

### Step 1: Compile the master evidence list

Organize all findings by trust level, then by date. This is your raw evidence base.

### Step 2: Identify "Says vs. Actually" gaps

For each substantive claim about the subject, check: does the journal record (L1) agree with the press/transcript record (L4/L5)?

Common divergence patterns to look for:
- **Dates that differ** between sources
- **Roles or relationships described differently** (who did what, who was involved)
- **Motivations that shift** across tellings (why something happened)
- **Details in journals but absent from press** (the private reality)
- **Details in press but absent from journals** (the performed narrative, the journalist's invention, or the strategic omission)
- **Repeated phrases across transcripts** (rehearsed talking points vs. organic recollection)

### Step 3: Identify what is missing

What would you expect to find about this subject that no source mentions? Be specific. List these as explicit gaps that future ingests could fill.

### Step 4: Determine page status

- If the subject has journal-backed claims and cross-confirmed facts -> `canonical`
- If based primarily on press/transcripts with no journal confirmation -> `working`
- If based on a single source -> `speculative`

---

## Phase 4: Write the diarization

Determine the output path based on type:

| Type | Path |
|------|------|
| person | `04_CANON/Shared/People/[Name].md` |
| place | `04_CANON/Shared/Places/[Name].md` |
| entity (practice-related) | `04_CANON/Practice/[Name].md` |
| entity (business) | `04_CANON/Business/Companies/[Name].md` |
| theme | `04_CANON/Practice/Themes/[Name].md` |

### Person template

```markdown
---
type: person
status: [canonical|working|speculative]
last_updated: YYYY-MM-DD
domain: [Practice|Business|Personal|Shared]
related_projects:
  - [project names]
related_places:
  - [place names]
aliases:
  - [if any]
---

# [Name]

[One-paragraph positioning statement. Who they are in relation to the vault owner's story. Source-cited.]

---

## How they met
[Narrative with dates and sources. If unknown, say so explicitly.]

## The relationship
[Key interactions, collaborations, documented conversations. Each claim source-cited with confidence marker.]

## Key role in the story
[What they contributed, influenced, enabled, or disrupted. Source-cited.]

## What they do
[Professional identity outside the vault owner's context. Source-cited.]

## Key facts
- [Bulleted, source-cited facts with confidence markers]

## Says vs. Actually
[Only include this section if divergences exist between source tiers.]

| Topic | Journal (L1) says | Press/Transcript (L4/L5) says | Assessment |
|-------|-------------------|-------------------------------|------------|
| [topic] | [journal evidence] | [press/transcript evidence] | [which is more reliable and why] |

## Open questions
- [Specific unknowns. What remains unresolved. What source would answer it.]

## Source notes
- [[relevant source note links]]

## Sources discovered (not yet in vault)
[Only include if web search found relevant external sources not already ingested.]
- [Title] — [URL] — [one-line: what this adds]

## See also
- [[related canon pages, projects, people, places]]
```

### Place template

```markdown
---
type: place
status: [canonical|working|speculative]
last_updated: YYYY-MM-DD
domain: [Practice|Business|Personal|Shared]
related_projects:
  - [project names]
---

# [Place Name]

[One-paragraph positioning. What this place is and why it matters.]

---

## Why it matters
[Role in the vault owner's story. Source-cited.]

## Key facts
- [Bulleted, source-cited facts]

## In the story
[Chronological narrative of the subject's connection to this place. Source-cited.]

## Cultural resonance
[What this place means beyond the operational facts. Source-cited.]

## Says vs. Actually
[Only if divergences exist.]

## Open questions
- [Specific unknowns.]

## Source notes
- [[links]]

## See also
- [[related pages]]
```

### Entity template

```markdown
---
type: entity
status: [canonical|working|speculative]
last_updated: YYYY-MM-DD
domain: [Practice|Business]
related_projects:
  - [project names]
related_places:
  - [place names]
---

# [Entity Name]

[One-paragraph positioning.]

---

## What it is / was
[Description. Source-cited.]

## Origin
[How it started. Source-cited.]

## Key facts
- [Bulleted, source-cited facts]

## In the timeline
[Chronological narrative. Source-cited.]

## Says vs. Actually
[Only if divergences exist.]

## Open questions
- [Specific unknowns.]

## Source notes
- [[links]]

## See also
- [[related pages]]
```

### Theme template

```markdown
---
type: theme
status: [canonical|working|speculative]
last_updated: YYYY-MM-DD
domain: Practice
---

# [Theme Name]

[One-paragraph definition. What this concept means in the practice's context.]

---

## What this means
[Expanded definition with source-cited examples.]

## Where it shows up
- [Bulleted list of projects, works, or events where this theme appears. Source-cited.]

## Relationship to other themes
- [[Other Theme]] — [how they connect]

## Evolution over time
[How this theme has changed across eras. Source-cited.]

## Limits and critique
[Where this theme breaks down or has been challenged. Source-cited.]

## Open questions
- [What remains unresolved about this concept.]

## Source notes
- [[links]]

## See also
- [[related pages]]
```

---

## Phase 5: Log and navigate

### Step 1: Log

Append to `00_HOME/Log.md`:

```
## [YYYY-MM-DD] diarize | [Subject Name]

- Type: [person/place/entity/theme] | Status: [canonical/working/speculative]
- Sources consulted: [count by tier — e.g., "2 journal, 0 file vault, 1 memoir, 3 articles, 2 transcripts, 4 source notes"]
- Says vs. Actually gaps: [count, or "none"]
- Open questions: [count]
- Output: [[path to new/updated page]]
```

### Step 2: Update Index.md

If the page is new, add a one-line entry to the appropriate section of `00_HOME/Index.md`.

### Step 3: Check inbound links

Use Grep to count how many files link to the subject's page name. If fewer than 3, list the top candidates for adding links (pages that mention the subject in their body text but do not wiki-link to this page).

---

## Escape hatches

- If **no sources** mention the subject at all -> **BLOCKED.** "No vault sources reference [subject]. Cannot diarize without source material. Consider ingesting relevant material first."
- If **only a single source** mentions the subject -> **DONE_WITH_CONCERNS.** Write the page but flag: "This page is based on a single source ([[source name]]). Status set to speculative. Ingest additional material to strengthen."
- If the user asks to diarize a subject that already has a rich, well-sourced page -> suggest /enrich instead unless they specifically want a fresh rebuild.
- If the source search produces more than 50 distinct mentions across the vault -> tell the user the scope before proceeding. This will be a large diarization. Confirm they want to proceed or narrow the focus.

---

## Completion

End with:

```
## Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
[one-line explanation if not DONE]
```
