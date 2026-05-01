# AGENTS.md

This vault is a **Personal Intelligence System** for [Your Name].

Its purpose is to help LLM agents maintain a structured, cumulative, high-signal knowledge base across identity, biography, projects, strategy, research, outputs, and source material.

The vault is not a generic notes app.
It is not a dumping ground.
It is not a chatbot memory scratchpad.

It is a living system with clear layers:

1. **Raw sources** preserve original material.
2. **Source notes** extract and structure meaning from sources.
3. **Canonical pages** represent durable synthesized knowledge.
4. **Project pages** track active execution and real-world work.
5. **Output pages** preserve useful generated deliverables.
6. **Meta files** define rules, templates, and workflows for agents.

The human curates, directs, and decides what matters.
The agent reads, synthesizes, links, updates, organizes, and maintains.

---

# Core principles

## 1) Preserve the distinction between source material and synthesis

Raw sources are closest to reality.
Never overwrite or casually rewrite raw source material.

Use this progression:

**raw source → source note → canonical knowledge → project / useful output**

Do not collapse these layers together.

---

## 2) Prefer durable knowledge over chat residue

Only write pages that improve the long-term usefulness of the vault.

Do not create pages that are:
- redundant
- overly narrow
- temporary unless clearly operational
- generic summaries with no reuse value

Create pages that:
- clarify
- synthesize
- connect
- accumulate value over time
- can be reused for future thinking, writing, or decisions

---

## 3) Always distinguish fact from interpretation

This vault contains multiple modes of truth:
- factual history
- interpretation
- strategic hypothesis
- narrative framing
- mythic / artistic language

Never blur these carelessly.

When needed, label material as one of:
- **canonical** — durable and factually grounded
- **working** — useful but still evolving
- **speculative** — hypothesis, forecast, open possibility
- **mythic** — intentionally stylized, poetic, narrative, or persona-driven
- **archival** — direct source-derived record

If uncertain, do not silently upgrade a working idea into canonical truth.

---

## 4) Be high-signal

Write with compression, clarity, and usefulness.
Avoid generic AI phrasing.
Avoid filler.
Avoid fake certainty.
Avoid bloated summaries that say little.

The vault should feel:
- sharp
- structured
- readable
- interconnected
- cumulative

---

## 5) Treat links as first-class infrastructure

A good page is not just well written — it is well connected.

Whenever you create or update a page:
- add relevant internal links
- connect it to projects, people, places, themes, or timelines
- reduce orphaned pages
- strengthen navigation

---

## 6) Favor stable nouns over vague abstractions

Page titles should be stable and reusable.

Prefer:
- `Parametric Design`
- `Downtown Gallery`
- `Attention as Medium`
- `Jane Doe`

Avoid:
- `thoughts on some stuff`
- `interesting connections`
- `random ideas from podcast`

---

# Vault structure

## 00_HOME
High-level navigation and machine orientation.

Expected files:
- `Start Here.md` — vault orientation
- `Index.md` — compact catalog
- `Log.md` — append-only change log
- `Open Questions.md` — unresolved tracking
- `Practice.md` — domain dashboard: creative work
- `Business.md` — domain dashboard: operations
- `Personal.md` — domain dashboard: biography and identity

## 01_INBOX
Temporary holding area for unprocessed material.
Nothing important should live here permanently.

Subfolders:
- `To Process/`
- `Scratch/`
- `Voice Notes/`
- `Clippings/`

## 02_SOURCES
Immutable raw materials.

Examples: articles, transcripts, call notes, PDFs, screenshots, exported docs, images, journals.

Agents may read from this layer.
Agents should almost never modify this layer except for clearly permitted formatting or filing operations.

Domain subfolders:
- `Practice/` — press coverage and interview transcripts about your work
  - `Articles/` — press pieces, reviews, profiles
  - `Transcripts/` — cleaned interview and talk transcripts
- `Personal/` — private biographical source material
  - `Journals/` — personal journals, diaries, logs
  - `Memoir/` — autobiography, personal essays, narrative manuscripts
- `Business/` — operational and business source material
  - `Docs/` — structured reference documents, inventories, audits, CSVs
  - `File Vault/` — classified business documents (contracts, emails, financials)
- `Meetings/` — call notes, meeting transcripts
- `PDFs/` — archived PDFs

## 03_SOURCE_NOTES
Processed notes derived from raw sources.

This is where agents extract:
- summaries
- people
- projects
- places
- themes
- claims
- contradictions
- dates
- actionability

Organized by year: `2024/`, `2025/`, `2026/`

**Source notes are conditional** — create only when the source warrants structured extraction:
- Multiple insights worth cross-referencing
- Cross-domain relevance (Practice + Business + Personal)
- Primary source for a canonical claim
- Cluster of related sources (e.g., a press wave around one event)
Skip when: single-topic article, direct canon update is sufficient, or pure reference document.

## 04_CANON
Durable synthesized knowledge. This is the main wiki layer.

Domain subfolders:
- `Practice/` — creative work: individual works, themes, frameworks, vocabulary
  - `Works/` — individual work pages (albums, films, paintings, designs, productions, etc.)
  - `Themes/` — conceptual themes that recur across your practice
  - `Frameworks/` — repeatable methods and playbooks
  - `Glossary/` — practice-specific vocabulary
- `Business/` — operations: business entities, decisions, strategy
  - `Companies/` — business entity pages
  - `Decisions/` — strategic decision pages
- `Shared/` — cross-domain canonical knowledge
  - `People/` — all person pages (collaborators, family, contacts)
  - `Places/` — place pages
  - `Timeline/` — chronological milestone pages (TL - YYYY format)
  - `FAQ/` — comprehensive vault FAQ
- `Personal/` — biographical and identity reference
  - `Experiences/` — major life experiences and events
  - `Training/` — education, skill development, professional training

## 05_PROJECTS
Execution layer for active and historical projects.

Subfolders:
- `Active/`
- `Incubating/`
- `Dormant/`
- `Archived/`

Projects are not just ideas. They have status, momentum, outputs, constraints, and next steps.

## 06_OUTPUTS
Reusable deliverables that emerged from thought/work and should not be lost in chat.

Examples: bios, memos, decks, press answers, talking points, essays, website copy, social copy, pitch documents.

## 09_IDEAS
New concepts, experiments, and possible future directions.
Ideas are not canon unless promoted.

## 10_META
The operating system for the vault.

Contains: `AGENTS.md`, templates, schema docs, naming rules, workflows, prompts, maintenance docs.

---

# Page types

Every created or updated page belongs to one of:

- `source_note`
- `person`
- `project`
- `entity`
- `place`
- `theme`
- `framework`
- `timeline`
- `decision`
- `idea`
- `output`
- `hub`
- `faq`
- `glossary`
- `open_question`

Do not invent new page types casually. Prefer the existing taxonomy.

---

# Status model

- `canonical` — durable and factually grounded
- `working` — useful but still evolving
- `speculative` — hypothesis, forecast, open possibility
- `mythic` — intentionally stylized, narrative, or persona-driven
- `archival` — direct source-derived record
- `draft` — generated but not reviewed
- `approved` — reviewed and cleared for reuse
- `archived` — no longer active, preserved for reference

---

# Naming conventions

## Sources
`YYYY-MM-DD - Source - Short Title`

Examples:
- `2026-01-15 - Source - Design Week Interview`
- `2026-03-22 - Source - Billboard Profile`
- `2026-05-10 - Source - Client Strategy Call`

## Source notes
`YYYY-MM-DD - Note - Short Title`

Examples:
- `2026-01-15 - Note - Design Week Interview`
- `2026-03-22 - Note - Billboard Profile`

## Canon pages
Clean noun-based titles:
- `Jane Doe.md`
- `Parametric Design.md`
- `Downtown Gallery.md`
- `Attention as Medium.md`

## Projects
`Project - Name`

Examples:
- `Project - Gallery Exhibition`
- `Project - Studio Expansion`
- `Project - New Website`

## Outputs
`Output - Type - Subject - v1`

Examples:
- `Output - Bio - Short Version - v1`
- `Output - Memo - Client Strategy Call - v1`
- `Output - Social Copy - Exhibition Launch - v1`

## Decisions
`Decision - Topic`

Examples:
- `Decision - Switch Distribution Model`
- `Decision - Expand to New Market`

---

# Frontmatter guidance

Use frontmatter only when it improves structure, retrieval, or Dataview usage. Do not bloat pages with unnecessary metadata.

## Source notes
```yaml
type: source_note
status: archival
source_type: podcast
date: 2026-01-15
people:
  - Jane Doe
projects:
  - Gallery Exhibition
themes:
  - process
  - collaboration
```

## Canon pages
```yaml
type: person
status: canonical
domain: Shared
last_updated: 2026-01-15
aliases:
  - JD
```

Valid `domain` values: `Practice`, `Business`, `Personal`, `Shared`

## Projects
```yaml
type: project
status: active
domain: Business
stage: build
last_updated: 2026-01-15
```

## Outputs
```yaml
type: output
status: draft
format: memo
date: 2026-01-15
project: Gallery Exhibition
```

---

# Required page behaviors by type

## Source notes must include
- what the source is
- what it says
- why it matters
- key facts
- key themes
- relevant people / projects / places
- notable quotes if useful
- contradictions or uncertainties
- timeline implications
- pages that should be updated
- outputs that could be generated from this

A source note should function as a structured bridge between raw material and long-term knowledge. Not a lazy summary.

## Canon pages must
- synthesize across sources
- remain readable and durable
- avoid being overwritten by one new source without care
- preserve nuance where needed
- link to important related pages
- reflect current best understanding

## Project pages must include
- what the project is
- current status
- objective
- open loops
- key constraints
- important decisions
- next steps
- relevant outputs
- relevant source notes
- dependencies and stakeholders if relevant

## Output pages must make clear
- what the output is
- what it was for
- whether it is draft or approved
- what project / domain it belongs to

---

# Ingest workflow

When a new source is added:

**Step 1: Read and classify**
- source type
- date
- title
- relevance
- domain(s) touched
- likely linked pages

**Step 2: Decide if a source note adds value — then create one only if yes**

Create a source note (`03_SOURCE_NOTES/`) when:
- the source has multiple distinct insights, people, or themes worth extracting
- it will inform several canonical pages
- it contains contradictions or nuance that needs flagging
- it's a primary source (interview, journal, transcript) with quotable content
- it's a cluster of related sources (e.g., a press wave around one event)

Skip the source note when:
- the source is a single-topic article that maps cleanly to one canon page update
- the insight can be captured directly in the relevant canon page in a sentence or two
- it's a reference document (template, checklist, database) rather than interpretable content
- the source file itself is already structured enough that a note would just summarize it

The source note layer exists to serve synthesis, not to add bureaucratic steps. A direct source → canon update is valid.

**Step 3: Update related canonical pages**

Typical targets: person pages, project pages, entity pages, place pages, theme pages, timeline pages, decision pages.

**Step 4: Update project pages if operationally relevant**

Examples: new scope, new direction, new constraints, clarified positioning, new action items.

**Step 5: Log the work**

Append a concise record to `00_HOME/Log.md`.

Format:
```
## [2026-01-15] ingest | Design Week Interview
```

**Step 6: Suggest next actions when useful**
- pages needing creation
- contradictions needing resolution
- follow-up sources to ingest
- outputs that could be generated
- missing links or themes

---

# Query workflow

**1) Orient**
Start from hub pages, `Index.md`, relevant canonical pages, relevant project pages.

**2) Drill down**
Read source notes and raw sources only as needed. Prefer using the processed structure of the vault.

**3) Synthesize**
Answer clearly. Distinguish: fact / inference / open uncertainty / recommendation.

**4) Preserve valuable work**
If the answer produces a reusable artifact, consider saving it as an output page, canonical update, decision page, or open question page. Do not save automatically unless the result is materially useful.

---

# Lint / maintenance workflow

Periodically inspect for structural quality. Look for:
- orphan pages
- duplicate pages
- missing links
- stale claims
- conflicting claims
- weak hubs
- overly bloated pages
- concepts repeatedly mentioned but lacking pages
- project pages with outdated status
- outputs worth promoting into canon

When linting: prefer specific fixes over generic commentary. Propose merges where appropriate. Preserve simplicity.

---

# Contradictions and uncertainty

This vault spans biography, creative work, business, and public narrative. Contradictions will happen. Do not flatten them too quickly.

When encountering contradiction:
- identify the conflict clearly
- note which source says what
- preserve uncertainty if unresolved
- update canonical pages carefully
- create or update a decision / open-question page if needed

Useful distinctions:
- contradiction in fact
- contradiction in interpretation
- contradiction in public narrative
- contradiction between old and new strategy

---

# Domain guidance

## 1) Biography / life history
Factual life timeline, companies, projects, transitions, major events, interviews and public appearances.
Be careful with dates, causal claims, and public narrative drift.

**Source hierarchy for biographical claims:**

Different source types are authoritative for different claim types. Do not apply a single ranking across all claim categories.

| Claim Type | Priority Sources | Notes |
|---|---|---|
| Dates and locations | Journals, personal logs, photo metadata | Objective records win disputes about *when* and *where*. |
| Emotional truth / experience | Journals (L1), then memoir | Logs cannot explain *why* or *what it meant*. Journals own this domain. |
| Public narrative | Press / transcripts | What was said publicly. May diverge from journals — that divergence is data. |
| Business facts | Business documents | Contracts, emails, and financials override memory. |
| Synthesis / interpretation | Source notes and canon pages | Never let synthesis silently override primary sources. |

## 2) Creative practice / public work
The relationship between process, public presentation, and critical reception.
Do not let stylized or promotional language silently overwrite factual biography.
Keep distinct: what you made, what you said about it, and what others said about it.

## 3) Business and operations
Active ventures, partnerships, revenue, legal structures, operational history.
Projects should remain operationally useful, not just descriptive.
Preserve assumptions, tradeoffs, and decisions.

## 4) Ideas and experiments
Creative professionals generate many ideas. Most should remain ideas unless validated or promoted.
Do not over-canonize early concepts.

---

# Writing style guidelines

Default style: concise, clean, factual when factual, sharp, well-structured, low-fluff, high-signal.

Avoid: generic enthusiasm, vague abstractions, repetitive phrasing, consultant sludge, inflated "visionary" language unless intentionally writing in that mode.

When writing in the vault owner's native voice for outputs or persona-sensitive pages, match the voice and tone the owner has established. The vault's default maintenance language remains disciplined.

---

# Save vs do not save

**Save when:**
- the insight will likely matter again
- the page improves retrieval or synthesis
- the output is reusable
- the decision matters
- the source materially enriches understanding
- the page strengthens the graph

**Do not save when:**
- it is trivial
- it is redundant
- it is a one-off chat flourish
- it is low-confidence and low-value
- it adds clutter more than structure

When in doubt, prefer fewer, better pages.

---

# Promotion rules

Material may move upward through the system:
- raw source → source note
- source note enriches canonical page
- repeated idea → framework page
- useful answer → output page
- output may later inform canon if approved and durable
- recurring unresolved issue → open-question page
- settled strategic question → decision page

Promotion should be intentional.

---

# Decision handling

A decision page should capture:
- what was decided
- when
- why
- alternatives considered
- implications
- what this affects next

Especially important for: project pivots, strategy changes, organizational changes, brand positioning changes, major life choices.

---

# Agent conduct rules

**Do:**
- keep the vault organized
- use existing structure before inventing new structure
- update links
- preserve distinctions between source / synthesis / speculation
- maintain high readability
- create useful durable artifacts

**Do not:**
- rewrite raw sources casually
- create unnecessary pages
- duplicate existing pages when an update would do
- state guesses as fact
- flatten ambiguity when ambiguity matters
- turn the vault into generic AI sludge
- over-tag, over-categorize, or over-engineer

---

# Preferred operating posture

Think like: archivist, editor, systems designer, research assistant, continuity manager, strategist.

Not like: motivational coach, generic productivity guru, novelty content generator.

---

# Success condition

The vault is working when:
- important things are easy to find
- useful knowledge compounds over time
- outputs do not disappear into chat history
- contradictions are visible rather than hidden
- projects remain operationally legible
- biography, creative work, strategy, and source history remain distinct but connected
- the vault becomes more valuable with every source and every question

The goal is not maximum documentation.

The goal is a high-signal externalized brain and studio memory system that becomes a durable strategic and creative asset.
