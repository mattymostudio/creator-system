# Creator System — Ingestion Tools

A demo pack of the scripts I use to pull my scattered personal history —
photos, Facebook archive, ChatGPT chats, press clippings, email — into a
single Obsidian vault that I navigate with Claude Code.

This folder is a **working demo**. The scripts run. You can drop your own
data in and see the output. The real contact lists, names, and URLs have
been swapped for generic placeholders — you'll replace those with your own.

> Released under the MIT License (see [`LICENSE`](LICENSE)). Provided as-is,
> as a snapshot of how I wire my own creative archive together. Take what's
> useful, leave what isn't, change whatever you want. Attribution appreciated
> but not required.

---

## What this is

Six small pipelines. Each one takes a messy export from a platform you
already use and turns it into plain-text Markdown that Obsidian can read.

```
Your raw export              This kit                    Your vault
──────────────────           ───────────                 ─────────────
iPhone photo dump     →      photo-processor      →      photos + notes
Google Takeout        →      takeout-processor    →      people + timeline
ChatGPT export        →      chatgpt-ingest       →      topic index
Facebook archive      →      facebook-ingest      →      messages + contacts
Your press links      →      press-ingest         →      clean article archive
Granola meetings      →      granola-ingest       →      meeting notes
```

Once the vault is populated, Claude Code (running in the vault folder)
becomes a search-and-synthesis layer over your whole history.

---

## Two ways to use this kit

How you'll use these tools depends on whether you've already set up the
Creator System vault.

### Path A — You have the vault set up

You've copied the sibling `vault/` folder, personalized it, and are running
Claude Code from inside it. In this case:

- **You drive everything through Claude Code, not the terminal.** Open
  Claude Code in your vault root and say things like "pull my recent
  Granola meetings" or "ingest this Facebook archive." Claude runs the
  right script and lands the output in the correct vault folder.
- **Use the vault-integration scripts.** These are the real endpoints:
  - `photo-processor/scripts/backfill_vault.py` — writes photo events
    into `02_SOURCES/Photos/`
  - `takeout-processor/05_scripts/vault_integrate.py` — writes contact
    notes into `04_CANON/Shared/People/`
  - `press-ingest/ingest_to_vault.py` — writes press articles into
    `02_SOURCES/Articles/`
  - `granola-ingest` — two-step skill; the second step synthesizes notes
    into `02_SOURCES/Meetings/`
- **Re-running is incremental.** Add a new Takeout export or photo dump,
  re-run, and new material merges into your existing notes rather than
  overwriting them.
- **Output shows up immediately** in Obsidian and is readable by Claude
  in your vault session.

### Path B — You don't have the vault yet

You downloaded this kit to see what it does, or to use one specific tool
(e.g., "just sort my camera roll"). In this case:

- **You run the scripts directly from the terminal.**  
  `cd` into a tool folder, then `python3 <script>.py`. No Claude Code
  required, though it still helps for debugging.
- **Output lands in local folders** — `parsed_domains/`, `Organized/`,
  `press-html/`, `your_fb_archive/`. Just files on disk, useful on their
  own.
- **Skip the vault-integration scripts.** They point at vault paths that
  don't exist on your system. They'll fail with "path not found" —
  that's fine, just don't run them.
- **When you're ready for the full system**, head up one level to
  [`../Standard Operating Procedure.md`](../Standard%20Operating%20Procedure.md)
  and [`../README.md`](../README.md) in the parent `creator-system/`
  folder. That's where the vault setup lives. Come back to these tools
  once your vault is running and switch to Path A.

The 10-minute Quick Start below works on either path — it uses
`chatgpt-ingest` as the intro, which is vault-agnostic.

---

## Who it's for

- Artists, writers, founders — anyone with a decade-plus of scattered
  personal archives they want to actually *use* again.
- You're comfortable running a command in the terminal.
- You've used (or are willing to install) **Obsidian** and **Claude Code**.
- You don't need to be a programmer. You will not be writing code.

If you've never opened Terminal, that's fine — walk through the Quick
Start below and you'll be fine. If you hit a wall, Claude Code itself can
help; it runs in whatever folder you point it at.

---

## What to install first

| Tool | Why | Where |
|---|---|---|
| **Obsidian** | Your vault lives here. | [obsidian.md](https://obsidian.md) |
| **Claude Code** | Drives the ingestion + browses the vault. | [claude.ai/code](https://claude.ai/code) |
| **Python 3.10+** | Most tools are small Python scripts. | Pre-installed on macOS; otherwise [python.org](https://www.python.org/downloads/) |
| **Homebrew** (macOS only) | For a couple of system dependencies. | [brew.sh](https://brew.sh) |

Optional, depending on which tools you run:

- **`tesseract`** — OCR for screenshots (photo-processor): `brew install tesseract`
- **`dlib` / `cmake`** — face detection (photo-processor): `brew install cmake`
- **Playwright** — browser automation (press-ingest): `pip install playwright && playwright install chromium`

You don't need all of these on day one. Each tool's folder says what *it*
needs.

---

## 10-minute Quick Start

This gets one tool running end-to-end so you can see the shape of things.

The simplest is **chatgpt-ingest** — no browser automation, no system
dependencies, just Python.

```bash
# 1. Open Terminal and cd into this folder
cd path/to/creator-system/tools/chatgpt-ingest

# 2. Run it against the sample data that ships with the kit
python3 parse_conversations.py

# 3. Look at the output
ls parsed_domains/
cat parsed_domains/art_park.json       # titles sorted into this domain
```

You should see a handful of JSON files in `parsed_domains/`, each one
holding the conversation titles the parser categorized into that domain
(art, real estate, memoir, finance, etc.).

Swap your real ChatGPT export in by replacing
`ChatGPT Download/conversations.json` with the `conversations.json` from
your [ChatGPT data export](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data).
Rerun. Done.

Every other tool works the same way: drop your real data in, run the
script, look at the output.

---

## How the pieces fit together

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│   tools/                                                 │
│   ├── tools/                                                       │
│   │   ├── photo-processor/         ← iPhone / photo dumps          │
│   │   ├── takeout-processor/       ← Gmail / Google contacts       │
│   │   ├── chatgpt-ingest/          ← ChatGPT exports               │
│   │   ├── facebook-ingest/         ← FB HTML archive               │
│   │   ├── press-ingest/            ← Press articles (URL list)     │
│   │   ├── granola-ingest/          ← Granola meeting notes         │
│   │   └── _shared/                 ← small cross-tool helpers      │
│   └── README.md                    ← you are here                  │
│                                                                    │
│                        ↓ each tool writes to ↓                     │
│                                                                    │
│   ../vault/                        ← the Obsidian vault            │
│   ├── 01_INBOX/                                                    │
│   ├── 02_SOURCES/                  ← press, photos, imports        │
│   ├── 04_CANON/Shared/People/      ← contact notes                 │
│   └── …                                                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

Each tool is **independent**. You can run one or all six. The order
doesn't matter much — they write to different parts of the vault and
don't depend on each other.

---

## The six tools

### 1. `photo-processor/` — iPhone photo dumps

Sorts a camera-roll dump by date and type (photo vs. screenshot vs.
video). Detects faces. OCRs screenshots. Clusters photos into events.
Generates an Obsidian note per event.

Most ambitious tool in the kit — plan on 15–30 min to get dependencies
installed. Once it's running, it'll chew through tens of thousands of
photos.

**Quick start:** `cd photo-processor && ./process.sh new --copy`

### 2. `takeout-processor/` — Gmail + contacts

Extracts one JSON "bundle" per contact from your Gmail archive (inside
your Google Takeout). Optionally enriches each bundle with a Claude API
call that summarizes the relationship. Rolls up to a master contact CSV,
a timeline of interactions, and a graph of who-knows-whom.

**Biggest tool.** Do chatgpt-ingest first; come back to this.

**Quick start:** drop Takeout zips in `00_raw_takeouts/`, then run the
stages in `05_scripts/` one at a time.

### 3. `chatgpt-ingest/` — ChatGPT conversation index

Parses your ChatGPT export (`conversations.json`) and sorts conversation
titles into topic buckets. Lightweight — uses no external services.
Great first tool to run because it ships with working demo data.

**Quick start:** `python3 parse_conversations.py`

### 4. `facebook-ingest/` — Facebook archive

Takes an HTML Facebook export, extracts every DM thread and every
post, and writes them as Obsidian notes. Ranks your contacts by message
frequency and outputs an Excel spreadsheet of your top connections.

**Quick start:** unzip your FB archive into `your_fb_archive/`, then
`python3 fb_to_obsidian.py`.

### 5. `press-ingest/` — press clippings archive

Given a list of article URLs, fetches each one, cleans the HTML,
screenshots it (via a real Chromium browser), falls back to the
Wayback Machine for dead links, and imports everything as Obsidian
notes. Useful for archiving your personal press footprint before URLs
rot.

**Quick start:** edit the URL list in `process_articles.py`, then
`python3 process_articles.py`.

### 6. `granola-ingest/` — meeting notes from Granola

Different shape from the others: it's a two-step *Claude Code skill*,
not a standalone Python script. You ask Claude Code (inside this folder)
to "run the granola-ingest pull step" and it uses the Granola MCP server
to fetch your recent meeting notes. A second step in your vault
synthesizes them into cleaned-up notes.

Requires **Granola** + the **Granola MCP server** hooked into Claude
Code. See `granola-ingest/README.md` for details.

---

## Running ingestion with Claude Code

Everything above works without Claude Code. But the whole point of the
vault is that **Claude Code running inside the vault folder** becomes a
single intelligent interface on your history.

Once any tool has populated the vault, open Claude Code in
`../vault/` and ask things like:

- *"What did I tell ChatGPT about Project X in 2024?"*
- *"Summarize my conversations with Alex Sample from our message archive."*
- *"Find every press mention of my work involving public sculpture."*
- *"Who have I talked to most in the last 12 months?"*

The ingestion tools' job is to get your data into a shape Claude can
read. Once it's there, Claude does the rest.

---

## Privacy notes

- **None of your real data ships with this kit.** Every hardcoded name,
  email, URL, and file path is a placeholder. You fill them in.
- **Your own data stays local.** The only tool that makes network calls
  is `takeout-processor/05_scripts/llm_enrich.py` — that one sends
  contact metadata to the Claude API for enrichment. It's opt-in.
  Everything else runs fully offline.
- **Don't commit real data back to git.** Each tool's folder has a
  `.gitignore` (or the pipeline folders are gitignored in the parent
  repo). Keep it that way — your Takeout mbox, your FB archive, and
  your photo dump are sensitive, even if they feel innocuous.

---

## Troubleshooting

| Problem | Try |
|---|---|
| "command not found: python3" | Install Python 3.10+ from python.org |
| "No module named X" | `pip install X` — most tools list their deps in a `requirements.txt` or docstring |
| Photo-processor crashes on HEIC | `pip install pillow-heif` |
| Press-ingest hangs on scrape | First time? `playwright install chromium` |
| Anything else | Run `claude` in the tool's folder and paste the error — Claude Code is designed to debug itself |

---

## Customizing

Each script has placeholders like `Your Artist Brand`, `yourdomain.example`,
`your_fb_archive`. Search for those strings and replace with your own:

```bash
grep -rn "yourdomain.example" tools/
grep -rn "Your Artist Brand" tools/
```

You'll mostly be editing:

- `chatgpt-ingest/parse_conversations.py` — the topic keyword lists
- `facebook-ingest/fb_to_obsidian.py` — `OWNER_NAME`, `ARCHIVE_DIR`
- `press-ingest/process_articles.py` — `HEADLINES_URL` or the URL list
- `takeout-processor/05_scripts/*.py` — the "known self" email list

No code changes required beyond search-and-replace for your own name and
paths.

---

## Questions

The easiest way to get help is to open Claude Code in the `tools/`
folder and ask. This README, each tool's README, and the scripts
themselves are all within reach of the same Claude session.
