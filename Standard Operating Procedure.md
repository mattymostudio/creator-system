# Standard Operating Procedure

How to use your Personal Intelligence System — with or without AI.

---

## Part 1: Getting Started

### Step 1: Open the vault
Copy the `vault/` folder to wherever you keep projects. Open it in [Obsidian](https://obsidian.md) (free).

### Step 2: Set up Claude Code (recommended)
1. Install [Claude Code](https://claude.ai/claude-code)
2. Navigate to your vault directory in the terminal
3. The `.claude/` folder contains 11 pre-built skills that automate the heavy work
4. Edit `.claude/settings.local.json` — update the `VAULT=` path to your vault location
5. Initialize git: `git init && git add -A && git commit -m "initial vault setup"`
6. Say "let's go" — Claude will walk you through personalization

### Step 3: Personalize
Replace `[Your Name]` and placeholder text in:
- `CLAUDE.md` (root) — your name and practice description
- `00_HOME/Start Here.md` — add your key pages as they develop
- `10_META/AGENTS.md` — only the opening line needs your name

### Step 4: Gather your first sources
Read `Data Sources to Gather.md`. Start with whatever you have — journals, a work list, a few press articles. Drop them in `01_INBOX/To Process/`.

### Step 5: Your first ingest
Tell Claude: `/ingest` and point at a file. Watch how it classifies the source, decides whether to create a source note, updates canon pages, and logs the work.

Or do it manually — see the Manual Ingest Workflow below.

---

## Part 2: Daily Use

### When new material arrives
Drop it in `01_INBOX/To Process/`. That's it. Process it when you're ready.

### When you have an idea
Create a quick page in `09_IDEAS/` using the Idea template. Score it on the Idea Scoreboard when you have a minute.

### When you make a decision
Create a Decision page in `04_CANON/Business/Decisions/`. Capture: what, when, why, alternatives, implications.

### When you produce something reusable
Save it in `06_OUTPUTS/` — bios, memos, pitch decks, essays, social copy. If it took effort to create and you might need it again, it belongs here.

---

## Part 3: Weekly Maintenance (30-60 min)

Pick one day a week for vault hygiene:

1. **Process the inbox** — work through `01_INBOX/To Process/`. Ingest, file, or discard each item. Goal: empty inbox.
2. **Link audit** — open graph view (Cmd+G). Look for orphaned nodes. Add links.
3. **Open questions** — review `00_HOME/Open Questions.md`. Mark resolved ones. Add new ones.
4. **Project status** — read each active project. Update status, next steps, open loops. Move stale ones to Dormant.
5. **Run lint** — `/vault-lint` (or use the manual checklist below). Fix what it finds.

---

## Part 4: Workflows

### Ingest (with Claude Code)

```
/ingest [filename or description of what to process]
```

Claude reads the source, classifies it, decides whether to create a source note, updates relevant canon pages, logs the work, and suggests next actions.

### Ingest (manual)

1. **Read and classify** — source type, date, domain(s), people/projects/places mentioned
2. **File the source** — move from inbox to the correct `02_SOURCES/` subfolder. Rename to: `YYYY-MM-DD - Source - Short Title`
3. **Source note?** — Does the source have 3+ insights worth cross-referencing? Create a note in `03_SOURCE_NOTES/[year]/`. If it maps to a single canon update, skip the note.
4. **Update canon pages** — for each relevant page, add new information with source citation. Never overwrite — add alongside existing content.
5. **Log it** — append an entry to `00_HOME/Log.md`
6. **Next actions** — note any pages to create, contradictions found, or follow-ups needed

### Query (finding answers in the vault)

1. **Orient** — start from hub pages or Index
2. **Drill down** — read source notes and raw sources only as needed
3. **Synthesize** — distinguish: fact / inference / uncertainty / recommendation
4. **Preserve** — if the answer is reusable, save it as an output or canon update

### Maintenance / Lint (with Claude Code)

```
/vault-lint
```

Runs 10 structural checks and writes a report. Fix what it finds.

### Maintenance / Lint (manual checklist)

- [ ] Broken links — search for `[[links]]` that point to non-existent pages
- [ ] Stub pages — pages with fewer than 5 lines of content
- [ ] Duplicates — same name in different folders
- [ ] Orphans — canon/project/output pages with no inbound links
- [ ] Missing frontmatter — pages missing `type` or `status` fields
- [ ] Status mismatches — project status vs folder location (e.g., "active" project in `Archived/`)
- [ ] Naming violations — files not following naming conventions
- [ ] Concepts without pages — terms in 3+ files with no dedicated page
- [ ] Stale pages — `last_updated` more than 90 days ago
- [ ] Underlinked pages — canon pages with fewer than 2 outbound links

---

## Part 5: AI Skills Quick Reference

### Skills that change the vault

| Command | What it does | When to use |
|---------|-------------|-------------|
| `/ingest` | Process a raw source through the full pipeline | New material arrives |
| `/diarize [subject]` | Build a comprehensive canon page from all sources about a subject | You want a definitive page on a person, place, or concept |
| `/enrich [page]` | Fill out a thin canon page by finding all related sources | A page exists but is a stub |
| `/vault-lint` | Run 10 structural checks, write a report | Weekly maintenance |
| `/improve` | Analyze vault health, propose improvements to rules and templates | After a few weeks of use, when patterns emerge |
| `/recap` | Write a dated recap (what changed / next / loose ends) to `00_HOME/Log.md` | End of a work session |
| `/autoresearch [topic]` | Run an autonomous research loop on an external topic; build a page in `08_RESEARCH/` | You want deep world-knowledge on something outside your personal canon |
| `/granola [pull.json]` | Synthesize a Granola meeting pull into the rolling archive in `03_SOURCE_NOTES/` | After running the `granola-ingest` tool from the Ingestion Tools pack |

### Skills that analyze (read-only)

| Command | What it does | When to use |
|---------|-------------|-------------|
| `/emerge` | Surface patterns the vault implies but never stated | Discover what the vault knows that you don't |
| `/challenge [belief]` | Pressure-test a belief against the vault's own evidence | Before committing to a strategic position |
| `/connect [A] [B]` | Find hidden bridges between two topics | Cross-pollination, non-obvious relationships |
| `/drift` | Compare stated priorities vs actual activity | When you suspect a gap between intention and execution |
| `/ideas` | Vault-wide brainstorm grounded in what the vault knows | Generate actionable ideas across all domains |
| `/council [topic]` | 12 professional personas evaluate a project/idea/deal | Before committing significant resources or reputation |

---

## Part 6: Source Hierarchy

When sources disagree, this is who wins:

| Level | Name | What | Authority |
|-------|------|------|-----------|
| L1 | Ground Truth | Journals, personal logs, photo metadata | Highest — what actually happened |
| L2 | Operational | Business docs, contracts, financials | Hard evidence for dates and amounts |
| L3 | Reflective | Memoir, personal essays | Events reliable, interpretation is perspective |
| L4 | External | Press, reviews, articles about you | Journalist-framed, may contain errors |
| L5 | Performed | Interviews, talks, podcasts by you | What you chose to say publicly |
| L6 | Prior Synthesis | Source notes, canon pages | Agent-generated — verify against primaries |

**Rule of thumb:** Business documents win for *what happened*. Journals win for *what it meant*. Press tells you *what others think happened*.

---

## Part 7: If You Get Stuck

**"I don't know where to put this."**
- Raw material from outside → `02_SOURCES/`
- Your processing of that material → `03_SOURCE_NOTES/`
- Durable knowledge → `04_CANON/`
- Active project with next steps → `05_PROJECTS/`
- Deliverable you might reuse → `06_OUTPUTS/`
- Half-formed thought → `09_IDEAS/`
- Truly can't classify → `01_INBOX/To Process/`

**"I don't have Claude Code."**
Every workflow above has a manual equivalent. The vault structure, templates, and AGENTS.md work without AI. AI makes it faster, but the system is designed to run by hand.

**"I don't have much source material yet."**
Start with whatever you have. Even 3-5 sources is enough to start building canon pages and seeing the system work. It compounds over time.

**"My vault feels messy."**
Run `/vault-lint` or use the manual checklist. The system is self-healing — regular maintenance keeps it sharp.
