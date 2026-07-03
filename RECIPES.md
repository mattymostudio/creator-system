# Things to Try

A recipe book. Pick one. Each entry takes something you probably already have, walks you through what to do with it, and ends with a tangible artifact — a page in your vault, a CSV you can open, an HTML map, a memo, a publishable bio.

Designed so you can scan this list during a coffee break, pick one, and have something to show by lunch.

> **Convention:** every recipe lists **Input → Tool → Skill → Output**. If a step has nothing in it (e.g., the recipe is skill-only), it'll say "—".

---

## How to use this list

Pick a recipe based on **what you already have on disk**, not on what skill sounds cool. The fastest path to "ohhh, this is actually useful" is to put your own data through one full cycle.

The recipes are grouped by **input type**, then a final section by **goal** if you want to work backwards from "I need to ship a bio."

If you get stuck mid-recipe: run `/vault-lint` to confirm the system is healthy, then re-read the step you got stuck on. Most failures are skipped steps.

---

## Photos

You probably have the densest archive here — phone, camera, screenshots, Drive, iCloud. Photos carry timestamps, locations, faces, and event context. They turn the vault from "things I wrote" into "things I lived."

### Recipe 1 — Map every place you've been

**Goal:** A CSV of every location you've taken a photo, ready for a map view.

| | |
|---|---|
| Input | A folder of photos with EXIF data (iPhone dump, camera SD, Google Photos export) |
| Tool | `photo-processor/scripts/extract_locations.py` |
| Skill | — |
| Time | 15 min |

**Steps:**
1. Drop your photo folder into `tools/photo-processor/new/`.
2. Run: `python3 scripts/extract_locations.py`
3. Open the output: `<organized-dir>/locations.csv`. Each row is one photo with lat/lon/date.

**What you get:** `locations.csv` — drag this into [kepler.gl](https://kepler.gl) or [umap.openstreetmap.fr](https://umap.openstreetmap.fr) for a free, browser-based interactive map of your life in dots. No accounts, no upload limits for normal-sized exports.

**Stretch (cohort bonus):** the `location-analysis/` pipeline turns this CSV into 15+ vault pages — decade maps, travel extremes, biome breakdowns, "where was I on 2014-06-12," art pilgrimage routes. Reach out if you want a copy.

---

### Recipe 2 — Sort the camera roll into events

**Goal:** Stop scrolling through 40,000 photos. See your life as event clusters.

| | |
|---|---|
| Input | A messy photo folder (10K+ photos works best) |
| Tool | `photo-processor/scripts/event_cluster.py` |
| Skill | `/diarize` (optional, after) |
| Time | 30–60 min for the run; 15 min review |

**Steps:**
1. Run: `python3 scripts/event_cluster.py /path/to/photos`
2. The tool clusters photos by date + location proximity. Output is folders like `2024-06-15 — Brooklyn — 47 photos`.
3. Open one cluster you remember. Confirm the system got the event right.
4. (Optional) Run `/diarize <event name>` to build a canon page about that event using everything in your vault that mentions it.

**What you get:** Your photo archive becomes a chronology of events instead of a chronological dump. Plus a `diarized` page that ties the photos to whoever was there, what was happening, and what came next.

---

### Recipe 3 — Extract every screenshot you've taken

**Goal:** A separate folder of just screenshots — usually 30%+ of a phone's photos. These are mostly recipes, plane tickets, books, screenshots of articles, and ideas you forgot you saved.

| | |
|---|---|
| Input | Phone photo dump |
| Tool | `photo-processor/scripts/extract_screenshots.py` + `screenshot_report.py` |
| Skill | `/ingest` (optional, on the report) |
| Time | 20 min |

**Steps:**
1. `python3 scripts/extract_screenshots.py /path/to/photos`
2. `python3 scripts/screenshot_report.py` — generates a Markdown report of what's in there (categorized: travel, food, reading, ideas, work, etc.)
3. Drop the report into `01_INBOX/To Process/` and run `/ingest`.

**What you get:** A canon page of "things I've cared enough to screenshot." Often surprising — surfaces themes you didn't know you were obsessed with. Real example from my vault: I had 280 screenshots of book covers I never bought.

---

### Recipe 4 — The face/place graph

**Goal:** Photos linked to canon pages of people and places. So a person page automatically shows up with photos of them.

| | |
|---|---|
| Input | Photo dump + your vault with some `04_CANON/Shared/People/` pages |
| Tool | `photo-processor/scripts/detect_faces.py` + `entity_extractor.py` |
| Skill | `/enrich` |
| Time | 1 hr (90% the script run; 10 min curation) |

**Steps:**
1. `python3 scripts/detect_faces.py /path/to/photos` — clusters faces.
2. Manually label the top 10 face clusters with a person's name (one-time annotation cost).
3. `python3 scripts/entity_extractor.py` — joins face clusters with canon people pages.
4. Run `/enrich [Person Name]` on someone you have lots of photos of — adds a "Photos" section to their canon page with paths.

**What you get:** A person's canon page now lists every photo of them in your archive, dated. Powerful for memoir / bio work, eulogies (sorry), or just remembering when you last hung out.

---

## Email, Calendar, Contacts (Google Takeout)

This is the highest-ROI ingest. Takeout is huge but it's the receipt of who's been in your life and when.

### Recipe 5 — Build your real contact list

**Goal:** A single, deduped, prioritized contact list. Not Gmail's auto-collected mess — your *real* people.

| | |
|---|---|
| Input | Google Takeout (Mail + Contacts + Calendar) |
| Tool | `takeout-processor` (full pipeline) |
| Skill | — |
| Time | 2–3 hours (most is the script running) |

**Steps:**
1. Request Google Takeout for Mail, Contacts, Calendar. Wait for the email (~1 hour).
2. Drop the resulting `.zip`s into `tools/takeout-processor/00_raw_takeouts/`.
3. Run the pipeline:
   ```
   python3 05_scripts/mbox_extract_bodies.py
   python3 05_scripts/build_master_csv.py
   python3 05_scripts/match_contacts.py
   python3 05_scripts/build_relationship_graph.py
   ```
4. Open `03_master_csvs/relationship_graph.csv` — sorted by message volume + recency.

**What you get:** A CSV of every person you've actually corresponded with, ranked by how-much-they-matter (proxied by message count, calendar density, recency). You'll be surprised who's at the top. Ingest the CSV into your vault and you can `/diarize <name>` on anyone.

> Real example: from my Takeout, I rebuilt a 626-person collector list with $410K of reconstructed sales — half of whom I'd forgotten about. That CSV is now the spine of my collector outreach work.

---

### Recipe 6 — Ask the email archive a question

**Goal:** Treat 20 years of email as a searchable knowledge base.

| | |
|---|---|
| Input | Takeout-processed mbox |
| Tool | `takeout-processor/05_scripts/mbox_extract_bodies.py` |
| Skill | `/ingest` then `/diarize` |
| Time | 3 hours initial setup; instant after |

**Steps:**
1. Run `mbox_extract_bodies.py` to convert the mbox into per-message Markdown files.
2. Cherry-pick the 50 most-relevant emails on a topic (e.g., "every email about my 2014 show in Berlin").
3. Drop them in `01_INBOX/To Process/`. Run `/ingest`.
4. Run `/diarize "2014 Berlin show"`.

**What you get:** A canon page about that show with every email cited, dated, and the people involved cross-linked to their canon pages. The email archive becomes infrastructure instead of a graveyard.

---

## Press, articles, URLs

If you've ever been in print, this is the recipe that makes you stop losing track.

### Recipe 7 — Your press, archived forever

**Goal:** A folder of every article ever written about you, locally cached so it survives when the original goes 404.

| | |
|---|---|
| Input | A list of press URLs (from your bio file, Wikipedia, Google searches) |
| Tool | `press-ingest` |
| Skill | `/ingest` |
| Time | 30 min for 50 articles |

**Steps:**
1. Make a text file: `press-ingest/urls.txt` with one URL per line.
2. Run: `python3 process_articles.py`. It fetches, cleans, archives.
3. Run: `python3 ingest_to_vault.py`. Files land in `02_SOURCES/Articles/`.
4. Run `/diarize "Press"` to build a press timeline canon page.

**What you get:** Press articles as plain Markdown. Bylines, dates, outlets, content. Searchable in your vault forever, even after the outlet pulls the article.

> Real example: I've ingested 200+ articles about my own work going back to 2014. Half the original URLs are dead. The vault still has them. When I need a quote from a 2017 NYT piece, I `grep` instead of Google.

---

### Recipe 8 — Generate a press page for your website

**Goal:** A clean, dated, sortable press list ready to paste into your site.

| | |
|---|---|
| Input | Your press archive from Recipe 7 |
| Tool | — |
| Skill | `/diarize "Press"` then manual format pass |
| Time | 45 min |

**Steps:**
1. Have Recipe 7 done first.
2. Run `/diarize "Press"` — builds a comprehensive press canon page.
3. Open the page. Ask Claude: *"Reformat this as a press list for my website — outlet, headline, date, link."*
4. Save to `06_OUTPUTS/Website Copy/press.md` (or `.html`).

**What you get:** A ready-to-deploy press section. Update it by re-running on a fresh ingest.

---

## Meetings (Granola)

The fastest-decay archive of your life — meetings disappear into your memory the moment they end. Granola is the cheapest insurance policy you can buy.

### Recipe 9 — Your meeting history, synthesized

**Goal:** Your last six months of meetings as a single rolling thematic archive.

| | |
|---|---|
| Input | Granola export (JSON or per-meeting Markdown) |
| Tool | `granola-ingest` |
| Skill | `/granola` |
| Time | 30 min |

**Steps:**
1. Export from Granola (per-meeting Markdown is easiest).
2. Drop into `tools/granola-ingest/_inputs/`.
3. Run the ingest tool.
4. In Claude Code, run `/granola` — synthesizes new meetings into the rolling archive at `03_SOURCE_NOTES/<year>/<year> - Note - Granola Meeting Archive`.

**What you get:** A single source note that summarizes who you met with, what you discussed, what got decided, what's open. Re-run weekly — new meetings merge into the existing synthesis.

> Real example: I processed 271 meetings from Nov 2024 → Feb 2026 in one pass. The synthesis surfaced things I'd lost track of: when a particular project actually wound down (Oct 23 2025, not Jan 2026 like I'd been telling people), who I'd promised follow-up to and ghosted, recurring themes across unrelated meetings.

---

### Recipe 10 — Who am I meeting with, and is it the right people?

**Goal:** A drift report that compares stated priorities against actual calendar.

| | |
|---|---|
| Input | Granola archive (Recipe 9) + filled-in `00_HOME/Studio.md` and project pages |
| Tool | — |
| Skill | `/drift` |
| Time | 5 min |

**Steps:**
1. Have Recipe 9 done first; project pages should list current priorities.
2. Run `/drift`.

**What you get:** A brutal but honest report: stated priorities vs. how you actually spent your last 90 days. Surfaces "phantom execution" — projects you talk about but don't actually work on. Most people who run this once change their next week.

> Real example from my vault on 2026-04-29: drift surfaced 7 projects in "Active" status with zero execution evidence in 90 days. Reorganized my dashboard the same hour.

---

## AI conversations (ChatGPT)

You've already had thousands of conversations with an AI. Most of them you'll never reread. This recipe makes them indexable.

### Recipe 11 — What have I been thinking about?

**Goal:** Topic index of every ChatGPT conversation you've ever had.

| | |
|---|---|
| Input | ChatGPT export (Settings → Data Controls → Export) |
| Tool | `chatgpt-ingest` |
| Skill | `/emerge` (optional) |
| Time | 20 min |

**Steps:**
1. Export from ChatGPT (you'll get a `conversations.json`).
2. Drop into `tools/chatgpt-ingest/ChatGPT Download/`.
3. Run: `python3 parse_conversations.py`.
4. Output: `parsed_domains/` with conversations grouped by topic.
5. (Optional) Run `/emerge` on the topic index to surface patterns.

**What you get:** Your AI conversations as a thematic archive — "questions I keep returning to," "things I tried to figure out and never resolved." Combined with `/emerge`, it's a mirror of what's been on your mind.

---

## Social (Facebook archive)

Old Facebook is most people's longest continuous private journal. The export is a nightmare. The tool fixes that.

### Recipe 12 — Reconstruct a relationship from messages

**Goal:** Every message thread with one person, chronological, in plain text.

| | |
|---|---|
| Input | Facebook archive (Settings → Download Your Information) |
| Tool | `facebook-ingest` |
| Skill | `/diarize <person>` |
| Time | 45 min |

**Steps:**
1. Request your Facebook archive (HTML or JSON; JSON is easier to parse).
2. Drop into `tools/facebook-ingest/your_fb_archive/`.
3. Run: `python3 fb_to_obsidian.py`.
4. Output: a folder per person, chronological message thread inside.
5. Pick a person who matters. Drop their thread into `01_INBOX/To Process/`. Run `/ingest`. Then `/diarize <Their Name>`.

**What you get:** A canon page for that person that includes 10 years of message context. Useful for: writing a wedding toast, a eulogy, a long-overdue catch-up email, or just remembering how you became friends.

---

## Already-loaded vault (skill-driven)

These assume you've done at least 5 ingests already. The vault has enough to push back at you.

### Recipe 13 — Comprehensive page about a subject

**Goal:** One canonical page about a person, place, project, or theme — with every source cited.

| | |
|---|---|
| Input | Your vault, with 3+ sources mentioning the subject |
| Tool | — |
| Skill | `/diarize <subject>` |
| Time | 5–15 min |

**Steps:**
1. Pick a subject that comes up in multiple sources.
2. Run `/diarize <subject>`.
3. Open the resulting page. Read it. Edit any wrong inferences.

**What you get:** A definitive page you'll reference for years. Has frontmatter, source citations, themes, chronology. The next time someone asks you about this person/project/place, you start here.

---

### Recipe 14 — Pressure-test a real decision

**Goal:** 12 expert personas read your vault and stress-test something you're about to commit to.

| | |
|---|---|
| Input | A real decision you're 50/50 on |
| Tool | — |
| Skill | `/council <topic>` |
| Time | 5–10 min |

**Steps:**
1. Pick a real decision: a hire, a launch, a partnership, a price, a "should I publish this."
2. Run `/council <decision>`.
3. Read all 12 perspectives. Notice which 2 made you uncomfortable. Engage those.
4. Save the output to `06_OUTPUTS/Memos/` for the receipts.

**What you get:** A pressure test that's grounded in *your* archive (not internet generalities). Personas reference specific past experiences from your vault when relevant. Six months later when you doubt the decision, you have the receipts.

> Real example: I've used `/council` on three real decisions in the last 90 days. One of them (Path A vs B) is the council output I show in cohort tours.

---

### Recipe 15 — Surface what your vault implies

**Goal:** Patterns the vault contains that you've never articulated.

| | |
|---|---|
| Input | A vault with 30+ pages and at least 50 sources |
| Tool | — |
| Skill | `/emerge` |
| Time | 10 min |

**Steps:**
1. Run `/emerge`.
2. Read the patterns it surfaces.
3. For each pattern that resonates, decide: *create a canon page about this?* If yes, run `/diarize <pattern name>`.

**What you get:** New canon pages about themes that were always there but unnamed. This is the single most "magical" skill in the system — it tells you things about yourself you didn't know.

> Real example: `/emerge` surfaced "Identity as Medium" and "Institutional Fiction" as themes running through 12 years of my work. I'd never named those. Both became canon pages and now anchor the artist statement on my website.

---

### Recipe 16 — Connect two things that don't seem related

**Goal:** Find the bridge between two topics in your archive.

| | |
|---|---|
| Input | A loaded vault |
| Tool | — |
| Skill | `/connect <A> <B>` |
| Time | 5 min |

**Steps:**
1. Pick two topics: a recent project + an old one. Or a person + a place. Or two themes that feel unrelated.
2. Run `/connect <A> <B>`.

**What you get:** Often a useful answer ("here are 3 ways these are related"), occasionally an essay you didn't know you had to write. The "huh" moments compound — file them in `09_IDEAS/`.

---

### Recipe 17 — Generate ideas grounded in your data

**Goal:** Brainstorm that's actually about you, not generic GPT output.

| | |
|---|---|
| Input | A loaded vault |
| Tool | — |
| Skill | `/ideas` |
| Time | 10 min |

**Steps:**
1. Run `/ideas`. (Or with a focus: `/ideas "things I could ship in 30 days"`.)
2. Score the results on `09_IDEAS/Idea Scoreboard.md`.
3. Move the top 1–2 to `05_PROJECTS/Incubating/`.

**What you get:** Ideas you actually might do, because they reference resources, contacts, and history that already exist in your vault. Not "you should start a podcast" generic stuff.

---

### Recipe 18 — External research, vault-aware

**Goal:** Deep-dive on a topic *outside* your vault, but linked back to your canon.

| | |
|---|---|
| Input | A topic you want to learn about |
| Tool | — |
| Skill | `/autoresearch <topic>` |
| Time | 20–60 min depending on depth |

**Steps:**
1. Run `/autoresearch <topic>`.
2. Output goes to `08_RESEARCH/_Active/<slug>/` with frontmatter linking back to relevant canon pages.
3. Review. If durable, mark it `status: stable`.

**What you get:** Structured research on the topic, with `linked_canon:` frontmatter so the next time you `/diarize` something connected, the research gets pulled in.

> Real example: I ran `/autoresearch` on 17 debt instruments to map small-business loan options. The output sits in research; the *decision* gets surfaced into my capital strategy framework on the next pass.

---

## Showcase outputs (publishable artifacts)

Recipes whose end product is something you can ship publicly.

### Recipe 19 — Bio refresh

**Goal:** Three bios — short, medium, long — for one audience type.

| | |
|---|---|
| Input | Vault canon pages about your career |
| Tool | — |
| Skill | `/diarize` (your name) → manual prompt |
| Time | 30 min |

**Steps:**
1. Run `/diarize <Your Name>` if you don't have a self-canon page yet.
2. Ask Claude: *"Using the canon page about me and recent press, write a 100/300/500-word bio for [audience]. The audience is a [conference / gallery / investor / podcast host]."*
3. Save to `06_OUTPUTS/Bios/`.

**What you get:** Three bios you didn't have to write from scratch. Update them by re-running on the latest vault. I have nine bios — three audiences (artist, business, conference speaker) × three lengths.

---

### Recipe 20 — A real talk, drafted from your archive

**Goal:** A 15-minute talk grounded in your actual life — not made-up examples.

| | |
|---|---|
| Input | A loaded vault, especially with strong canon pages on a few key topics |
| Tool | — |
| Skill | `/diarize` + manual brief to Claude |
| Time | 2–4 hours |

**Steps:**
1. Pick the throughline: *what's one thing I want this audience to walk away believing?*
2. Run `/diarize` on each topic the talk will reference. Build the canon spine first.
3. Brief Claude: *"Draft a 15-minute talk on <topic>. Beats I want to hit: [list]. Use only material from canon and source notes — no invented examples. Voice: [yours]."*
4. Iterate. Cut hard. Run `/challenge` on the strongest claim if it feels shaky.
5. Save to `06_OUTPUTS/Talks/`.

**What you get:** A talk that holds together because it's sourced. When someone asks a question that wasn't in the talk, the canon page is right there.

> Real example: I drafted my TED talk in two days using this pattern. Three variant drafts ("Unwalkable Moat" / "Identity Is a Material" / "In the Gap") synthesized into a hybrid. Total: ~6 hours including the research pass.

---

### Recipe 21 — Website that lives in your vault

**Goal:** Your public website's pages as Markdown / HTML files in `06_OUTPUTS/Website Copy/`. Edit the vault, push, deploy.

| | |
|---|---|
| Input | An existing site (or willingness to build one) |
| Tool | — |
| Skill | manual |
| Time | First setup: a weekend. Updates: 10 min. |

**Steps:**
1. Create `06_OUTPUTS/Website Copy/` if it doesn't exist.
2. Move (or copy) your site's HTML/Markdown there.
3. Add a deploy script (Vercel, Netlify, or `rsync` to your host).
4. Edit pages in Obsidian. Push. Deploy.

**What you get:** Your website is now in version control + edited where the rest of your work lives. When you `/diarize` a new artwork, you can copy the synthesis into the artist page in two clicks.

> Real example: my full artist website lives at `06_OUTPUTS/Website Copy/` — eight HTML pages, an `llms.txt` for AI discoverability, a sitemap, the whole thing. Updates to the artist page are now a vault edit, not a CMS chore.

---

### Recipe 22 — Newsletter draft

**Goal:** A weekly or monthly newsletter draft sourced from your last X days of activity.

| | |
|---|---|
| Input | A vault used regularly (with `/recap` entries in the log) |
| Tool | — |
| Skill | `/recap` (must have been running this) + manual brief |
| Time | 30 min |

**Steps:**
1. Pull the last 30 days of `/recap` entries from `00_HOME/Log.md`.
2. Brief Claude: *"From the last 30 days of my log, draft a 600-word newsletter for my subscribers. Voice: [yours]. Lead with the most interesting thing. Keep it concrete."*
3. Save to `06_OUTPUTS/Substack/` or wherever your newsletter lives.

**What you get:** A draft sourced from things you actually did this month, not generic content marketing. Edit, send, repeat.

---

### Recipe 23 — Memo to a stakeholder

**Goal:** A clean memo to an investor, partner, or client based on what's actually true today.

| | |
|---|---|
| Input | Vault with project pages + recent log entries |
| Tool | — |
| Skill | `/council` (optional, for stress-test) + manual draft |
| Time | 1 hr |

**Steps:**
1. Pull the project page + last 90 days of log entries about the project.
2. Brief Claude: *"Draft a 500-word memo to <stakeholder> summarizing where <project> stands. Lead with what's working, then risks, then asks. Use only material in canon — no aspiration."*
3. Optional: run `/council "Should I send this memo?"` for a stress-test.
4. Save to `06_OUTPUTS/Memos/`.

**What you get:** A memo that's grounded in what actually happened, not what you hoped happened. Keeps you honest with stakeholders.

---

## Your work archive (images)

### Recipe 24 — One hero image per work

**Goal:** A single canonical display image chosen for every work in your archive — ready for a website, catalog, or sales sheet.

| | |
|---|---|
| Input | An archive folder per work, each holding several photos of the same piece |
| Tool | `work-hero-picker` |
| Skill | — |
| Time | 15 min setup + however long the clicking takes |

**Steps:**
1. `cd tools/work-hero-picker && python3 build_picker.py --works-root path/to/archive` — generates a self-contained HTML picker with candidates auto-ranked (likely hero first).
2. Serve it: `cd path/to/archive && python3 -m http.server 8765`, open `http://localhost:8765/hero-picker.html`.
3. Click one image per work (or skip). Selections persist as you go. Click **Export selections** when done.
4. `python3 apply_selections.py ~/Downloads/hero-selections.json --web-root path/to/archive`.

**What you get:** A `_hero/` subfolder inside every work with a symlink to your pick — originals untouched. Downstream tools (Recipe 21's site, a catalog generator, an inventory export) can rely on `_hero/` holding exactly one image per work.

---

## By goal (cross-reference)

| If you want to … | Try recipe |
|---|---|
| See your life on a map | 1 |
| Stop losing meetings | 9 |
| Rebuild a contact list that matters | 5 |
| Find what you're obsessed with | 3, 11 |
| Make a publishable bio | 19 |
| Pressure-test a decision | 14 |
| Find connections you've missed | 16 |
| Generate ideas about your own work | 17 |
| Surface patterns you haven't named | 15 |
| Draft a talk grounded in your archive | 20 |
| Move your website into your vault | 21 |
| See if your calendar matches your priorities | 10 |
| Reconstruct a relationship | 12 |
| Make your press archive permanent | 7, 8 |
| Send a newsletter you don't have to write | 22 |
| Draft a memo that's actually true | 23 |
| Pick one display image per work | 24 |

---

## What's not in this list (yet)

A few recipes I've built or have on the roadmap but haven't packaged for the kit yet. Available to cohort members on request:

- **`location-analysis`** — turns the photo CSV into 17 vault pages: decade maps, travel extremes, "where was I on date X," art pilgrimage routes, biome breakdowns. Real working tool.
- **Mentor pass on a draft** — voice-match review against a mentor's body of work. Useful for essay polish.
- **Substack reply skill** — drafts contextual replies to comments using your vault.
- **Harvest skill** — pulls liked tweets / saved articles into the inbox automatically.
- **Patent / IP mining** — scans your archive for patent-able ideas you've casually mentioned.
- **Drift report v2** — adds a "phantom execution" detector.

These are the kind of things that will ship in future paid packs or as community contributions. If you build one, send a PR.

---

## Rules of the road

1. **Start with one source.** Five sources is enough for the system to do something useful. You don't need 200 to get value.
2. **Run `/recap` at the end of every session.** Otherwise you'll forget what you did and have to figure it out from the file tree.
3. **`/vault-lint` weekly.** It catches stub pages, broken links, duplicate names, stale frontmatter. The system is self-healing if you let it lint.
4. **Don't re-do work the system has already done.** Before writing a bio from scratch, search `06_OUTPUTS/Bios/`. Before writing a memo, check `06_OUTPUTS/Memos/`. Past you wrote the right thing, probably.
5. **The vault is the workshop, not the gallery.** Outputs are public. The vault is private. Don't share the vault folder; share the outputs that came out of it.
