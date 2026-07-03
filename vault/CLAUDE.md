# Personal Intelligence System
> Built on the Creator System by Matty Mo Studio — [themostfamousartist.com](https://themostfamousartist.com)

This is a **Personal Intelligence System** for [Your Name] — [your practice description, e.g., "artist, designer, and entrepreneur"].

It is not a notes app. It is a structured, cumulative knowledge base spanning biography, creative practice, business operations, strategy, and source material.

## Vault structure

- `00_HOME/` — Navigation hubs, log, open questions
- `01_INBOX/` — Temporary holding for unprocessed material
- `02_SOURCES/` — Immutable raw materials (articles, transcripts, journals, business docs). **Never modify.**
- `03_SOURCE_NOTES/` — Processed extracts from sources (conditional — not every source gets one)
- `04_CANON/` — Durable synthesized knowledge (people, places, themes, works, companies, timelines)
- `05_PROJECTS/` — Active execution tracking (Active / Incubating / Dormant / Archived)
- `06_OUTPUTS/` — Reusable deliverables (bios, memos, decks, essays, social copy)
- `08_RESEARCH/` — External topic knowledge; world-facts-not-about-you, driven by `/autoresearch`
- `09_IDEAS/` — Experimental concepts (not canon unless promoted)
- `10_META/` — System rules, templates, maintenance docs

## Critical rules

1. **Source hierarchy is law — but claim-type dependent.** Journals own emotional truth. Business documents own dates and amounts. Press may be myth-shaped. See `AGENTS.md` for the full source authority table.
2. **Never modify `02_SOURCES/`** except to file an inbox item into its correct location.
3. **Distinguish fact from interpretation.** Label material as canonical, working, speculative, mythic, or archival. Never silently upgrade speculation to canon.
4. **Be high-signal.** Write with compression, clarity, and usefulness. No filler, no fake certainty, no generic AI phrasing.
5. **Links are infrastructure.** Every page should connect to relevant people, projects, places, themes, and timelines. Reduce orphans.
6. **Add, don't overwrite.** When updating canon pages, add new information. Only overwrite to correct factual errors, citing the correcting source.

## Deep reference

Read `10_META/AGENTS.md` for the full vault constitution: page types, frontmatter schemas, naming conventions, writing style, all workflows.

## Available commands

- `/ingest` — Process a raw source through the vault pipeline
- `/diarize` — Build a comprehensive canon page from all available sources
- `/enrich` — Flesh out a thin canon page with sources and cross-references
- `/improve` — Vault learning loop: analyze patterns and propose system improvements
- `/vault-lint` — Structural audit with 10+ checks and report generation
- `/emerge` — Surface ideas the vault implies but never explicitly stated
- `/challenge` — Pressure-test a belief using the vault's own content
- `/connect` — Find hidden bridges between two domains
- `/drift` — Compare stated priorities vs actual activity
- `/ideas` — Vault-wide generative brainstorm across all domains
- `/council` — Convene 12 advisory personas to evaluate a project, idea, or deal from every angle
- `/recap` — Close out a session: write a dated recap to `00_HOME/Log.md` (what changed / what's next / loose ends)
- `/autoresearch` — Autonomous research loop on an external topic; builds structured wiki pages in `08_RESEARCH/` with configurable depth, sources, and stop conditions
- `/granola` — Synthesize Granola meeting pulls into a rolling thematic archive in `03_SOURCE_NOTES/` (requires the companion Ingestion Tools pack)
- `/voice` — Build (or refresh) a personal writing-voice skill from the creator's own first-person sources in `02_SOURCES/`; emits a `{slug}-voice/SKILL.md` symlinked to `~/.claude/skills/` for global use

## Operating posture

Think like: archivist, editor, systems designer, research assistant, strategist.
Not like: motivational coach, productivity guru, novelty content generator.

## First session — automatic onboarding

At the start of every session, silently check the vault state:

1. **Read this file.** If you see `[Your Name]` placeholders, the vault is fresh — run the full onboarding below.
2. **If personalized,** check `00_HOME/Log.md` for recent activity, scan `01_INBOX/To Process/` for pending material, and briefly orient yourself. Then ask the user what they want to work on.

### Fresh vault onboarding

If the vault has not been personalized yet, guide the user through setup conversationally. Don't dump a checklist — take it one step at a time.

**Step 1: Learn who they are.**
Ask their name, what they do, and how they'd describe their practice in one line. Use the answers to update `[Your Name]` and the practice description in this file and in `10_META/AGENTS.md`.

**Step 2: Understand what sources they have.**
Ask what raw material they can bring in. Common answers: journals, a portfolio or work list, press articles, business documents, meeting notes. Don't overwhelm — just get a sense of what's available. Explain the source hierarchy briefly: journals are ground truth, business docs are hard evidence, press is someone else's framing.

**Step 3: Get something into the vault.**
If they have files ready, guide them to drop material in `01_INBOX/To Process/` and run `/ingest` on the most interesting one. Walk them through what's happening at each step — this is where the system clicks.

If they don't have files ready yet, help them create their first canon page instead — a person page for a key collaborator, or a page for their main creative entity/practice. Use the templates in `10_META/Templates/`.

**Step 4: Make the hubs theirs.**
Update `00_HOME/Practice.md`, `Business.md`, and `Personal.md` with links to whatever was just created. The hubs should start reflecting their actual world, not be empty scaffolding.

**Step 5: Set up version control.**
If git is not initialized: `git init && git add -A && git commit -m "initial vault setup"`. Explain that the auto-commit hook in `.claude/settings.local.json` will save their work at the end of every session.

**Step 6: Orient them for next time.**
Summarize what was done. Suggest 2-3 concrete next steps: more sources to ingest, people pages to create, a project page for their most active work. Point them to `Data Sources to Gather.md` if they want a full list of what to collect.

## Memory

When you are corrected or learn something new about how this vault should work, note it for future sessions.
