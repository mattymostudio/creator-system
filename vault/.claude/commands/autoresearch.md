---
description: Run an autonomous research loop on an external topic. Configures depth, sources, and stop conditions via a control.yml file. Produces a structured wiki page in 08_RESEARCH/ with cross-references to canon. Use when you want to build up world-knowledge on a subject that isn't personal canon.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit, WebSearch, WebFetch, Agent
origin: matty-mo-studio-creator-system/1.0
---

# Autoresearch

You are running an autonomous research loop on an external topic. Your job is to iterate through web sources, synthesize findings into a structured research page, cross-reference against the vault, and stop when the topic is saturated or the stop conditions trip.

**Working directory:** vault root.

**Output lives in:** `08_RESEARCH/` (see `08_RESEARCH/README.md` for the folder layout).

---

## Non-negotiables

1. **Autoresearch writes only to `08_RESEARCH/` and `02_SOURCES/Research/`.** It never writes to `04_CANON/`. If a finding should update canon, surface it as a suggestion in Phase 6, don't act.
2. **Every claim must cite a source.** Use inline footnote-style citations `[^1]` linked to a sources list. No unsourced synthesis.
3. **Respect stop conditions.** When any condition in `control.yml` trips, halt immediately. Do not exceed `max_sources`, `max_passes`, or `max_runtime_minutes`.
4. **Detect saturation.** If the last N sources added no new concepts to the synthesis, stop. This is the primary signal that research is complete.
5. **Cross-reference on first mention.** Any vault entity named in the control file's `linked_canon` gets auto-linked `[[Entity]]` on first appearance in any section.
6. **Log every run.** Append to the topic's `log.md` and the vault's `00_HOME/Log.md`.

---

## LAWs (output-contract, anti-regression)

These are numbered hard rules pinned to specific past failures. If you are about to violate one, stop.

- **LAW 1 — Every claim is cited.** No unsourced synthesis. Unsupported assertions get deleted, not footnoted after the fact.
- **LAW 2 — No canon writes.** Autoresearch writes only to `08_RESEARCH/` and `02_SOURCES/Research/`. Canon updates are suggestions in Phase 6, not actions.
- **LAW 3 — The query plan precedes the fetch.** Phase 2a emits the JSON plan before any WebSearch fires. If `stop_after_plan: true`, print and exit.
- **LAW 4 — Phase 1.5 is mandatory.** Keyword-trap screen runs on every invocation. Log "clean" or "resolved X -> Y".
- **LAW 5 — Use ` - ` (hyphen with spaces), never em-dashes or en-dashes in emitted research pages.** Keeps diffs predictable.
- **LAW 6 — Frontmatter `confidence` must be recomputed each pass** from the current source mix. Stale confidence values are a lie.

### Dated failure log

Append dated entries when a run regresses. Future runs read this before writing.

- _(none yet)_

---

## Phase 1: Dispatch

The user invokes `/autoresearch` with one of:
- A topic slug pointing to an existing `08_RESEARCH/_Active/{slug}/control.yml`
- A topic name with no existing config — create a new topic
- No argument — list active topics from `08_RESEARCH/_Active/` and ask which to run

### Step 1a: New topic

If no config exists, ask the user for:
- Topic name
- Core question
- Depth (shallow / medium / deep)
- Cadence (one_shot / weekly / monthly)

Then:
1. Copy `10_META/Templates/research-control.yml` to `08_RESEARCH/_Active/{slug}/control.yml`.
2. Fill in the identity + depth + cadence fields.
3. Scan `04_CANON/` for entities that match keywords in the topic. Populate `linked_canon` with the top 3-5 matches, present to user for confirmation.
4. Proceed to Phase 2.

### Step 1b: Existing topic

Read `control.yml`. Confirm:
- Cadence allows a run now (e.g., if `cadence: one_shot` and `runs_completed > 0`, ask the user to confirm a re-run)
- `status` is not `archived`

Set `status: active`, record `last_run` start.

---

## Phase 1.5: Pre-flight disambiguation (keyword-trap check)

**Before any WebSearch fires**, screen the topic for ambiguity. A sloppy topic burns sources on the wrong thing. Check for:

- **Generic nouns** — "agents", "memory", "flow", "platform". Likely to collide with unrelated meanings.
- **Numeric collisions** — "4o", "Claude 4", "GPT-5". Version numbers drift and overlap.
- **Demographic shopping** — "best tools for founders", "what GenZ wants". Too broad to converge.
- **Overly literal phrases** — "the memory problem" may be philosophy, ML, or neuroscience.
- **Named entity homonyms** — person name that collides with a company, place, or product.

If any trigger fires, STOP and ask the user to pick a sharper framing. Propose 2-3 disambiguated variants. Only proceed once the topic resolves cleanly. Log the disambiguation in the topic log as "Phase 1.5: resolved [vague] -> [specific]".

If no trigger fires, note in the run log "Phase 1.5: clean" and proceed.

---

## Phase 2: Query plan + seed search

### Step 2a: Emit a query plan (JSON)

Before running WebSearch, emit a plan the user can inspect. This prevents burning tokens on misaligned queries.

```json
{
  "topic": "[resolved topic after Phase 1.5]",
  "intent": "GENERAL | NEWS | COMPARISON | RECOMMENDATIONS | DEEP_DIVE",
  "freshness": "live | 30d | 1y | evergreen",
  "cluster_mode": "single | per_entity",
  "subqueries": [
    {"q": "[broad overview query]", "purpose": "establish baseline"},
    {"q": "[specific terminology query]", "purpose": "surface jargon + authorities"},
    {"q": "[latest [topic] 2026 query]", "purpose": "freshness pass"},
    {"q": "[sub-question from output_sections]", "purpose": "target gap"}
  ],
  "source_bias": ["[preferred domains from control.yml]"],
  "stop_after_plan": false
}
```

If `stop_after_plan: true` is passed as an invocation flag, print the plan and exit without fetching. Default is false — plan then proceed.

### Step 2b: Execute the plan

1. Run WebSearch on each subquery in `subqueries`. Collect URLs.
2. Filter:
   - Respect `source_types` allowlist — drop URLs that don't match allowed categories
   - Apply `source_denylist`
   - Deduplicate by domain + path
3. Rank:
   - Preferred domains from `source_allowlist_preferred` float to the top
   - Higher-authority domains (.edu, .gov, established publications) rank above blogspam
4. Pull the top sources via WebFetch. Cap at `max_sources / max_passes` for this pass.

Save fetched raw text to `02_SOURCES/Research/{slug}/{YYYY-MM-DD}-{source-slug}.md` with frontmatter capturing URL, fetch date, and domain.

---

## Phase 3: Extract and outline

For each fetched source:
1. Identify which `output_sections` it contributes to.
2. Extract factual claims with page-locators or quotes.
3. Note contradictions against claims already synthesized.

Maintain a **concept ledger** — running list of distinct concepts / entities / claims seen so far. This powers the saturation check.

---

## Phase 4: Synthesize

Write or update the research page.

### Page location

- Single-file topic: `08_RESEARCH/_Active/{slug}.md`
- Folder topic (sections > 3): `08_RESEARCH/_Active/{slug}/{Topic}.md` + `sections/{section}.md` files

### Page template

```markdown
---
type: research
status: active
topic: [topic name]
depth: [depth]
cadence: [cadence]
confidence: low | medium | high
first_run: YYYY-MM-DD
last_updated: YYYY-MM-DD
runs_completed: N
source_count: N
linked_canon:
  people: [...]
  projects: [...]
  themes: [...]
---

# [Topic]

## Core question
[from control.yml]

## Summary
[3-5 sentence executive summary. Updated every pass.]

## TL;DR bullets
- [5-7 bullets, the load-bearing findings]

## [Section from output_sections]
[Synthesized content. Every claim cited.]

...

## Contradictions and open questions
[Surfaced tensions between sources.]

## Connections to vault
[Cross-references to canon entities this research touches. Not implicit suggestions to canon - just links.]

## Sources
Each citation carries a source-type tag. Tags: `primary | institutional | secondary | opinion | aggregator`.

[^1]: [`tag`] [Title] - [URL] - fetched YYYY-MM-DD
...
```

### Trust labeling rules

Research does **not** use the L1-L6 biographical hierarchy (that is for personal claims only). Research uses:

**Per-source tag** (applied inline):
- `primary` — subject speaks directly (paper, filing, founder interview)
- `institutional` — established journalism, academia, government
- `secondary` — analyst / commentator synthesis
- `opinion` — named thinker's argued position
- `aggregator` — lists, link dumps, summaries

**Page-level `confidence`** (frontmatter, derived from source mix):
- `high` — multiple primary/institutional sources converge
- `medium` — mixed, partial convergence
- `low` — mostly opinion/aggregator, or contradictions unresolved

Update `confidence` in the control.yml and page frontmatter on every pass based on the current source mix.

When content from this research is later promoted to canon (via `/enrich`), it enters canon as L4. The tag translation happens at the promotion boundary.

### Synthesis rules

- Prefer original wording over paraphrase. Use short quoted phrases (< 15 words) when the source's wording is load-bearing.
- Never reproduce paragraphs from sources. Rewrite in synthesis voice.
- Attribute competing claims: "X argues Y [^3], while Z counters that W [^7]."
- Flag uncertainty explicitly: "As of [fetch date], the consensus appears to be..."

---

## Phase 5: Iterate or halt

After Phase 4, check stop conditions:

| Condition | Check |
|---|---|
| `max_sources` | Total sources fetched across all passes |
| `max_passes` | Count of outer Phase 2-4 iterations |
| `saturation` | Last N sources added no new concepts to ledger |
| `max_runtime_minutes` | Wall-clock since run start |

**If none trip:** generate follow-up queries based on gaps (empty sections, open questions, under-cited claims). Return to Phase 2 with refined queries.

**If any trip:** proceed to Phase 6.

---

## Phase 6: Finalize and log

### Step 1: Update control.yml

- `last_run` = now
- `runs_completed` += 1
- `status`: keep `active` if cadence is recurring, else `stable` if saturation was the stop reason

### Step 2: Run cross-reference pass

Grep the vault for entities named in the research page. For any 3+ matches to a canon entity not already in `linked_canon`, add it and back-link on first mention.

### Step 3: Append to topic log

`08_RESEARCH/_Active/{slug}/log.md`:

```
## [YYYY-MM-DD] run #N
- Pass count: N
- Sources fetched: N (total: N)
- Stop reason: [saturation | max_sources | max_passes | max_runtime]
- New concepts added: [count]
- Contradictions surfaced: [count]
- New canon cross-refs: [[...]]
```

### Step 4: Append to vault log

`00_HOME/Log.md`:

```
## [YYYY-MM-DD] autoresearch | [topic]
- Sources: N | Stop: [reason]
- Research page: [[Topic]]
- Canon suggestions: [list, if any]
```

### Step 5: Surface suggestions (do not act)

List:
- **Canon pages that could benefit** — specific findings that would strengthen existing `04_CANON/` entries, with the exact link to feed to `/enrich`
- **Project implications** — if research touches an active project, name the project and the implication
- **Follow-up research topics** — gaps this research identified that would warrant their own `/autoresearch` topic
- **Contradictions needing resolution** — where sources disagree, name the tension

---

## Escape hatches

- If WebSearch / WebFetch return no usable results after seed pass — **BLOCKED.** "Could not source material for topic. Try reframing the query."
- If all fetched sources are denied by content filters — **BLOCKED.** Report and halt.
- If control.yml is malformed — ask the user before proceeding; do not silently patch.
- If a topic already has `status: archived`, refuse to run unless user explicitly overrides.

---

## Completion

End with:

```
## Status: [DONE | DONE_WITH_CONCERNS | BLOCKED]
- Stop reason: [...]
- Sources this pass: N
- Research page: [[Topic]]
- Next suggested action: [one line]
```
