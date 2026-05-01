# press-ingest

Given a list of article URLs, scrapes each one, cleans the HTML,
screenshots it in a real browser, and falls back to the Wayback Machine
for dead links. Useful for archiving your personal press footprint
before URLs rot.

## Setup

```bash
pip install requests beautifulsoup4 trafilatura playwright lxml
playwright install chromium
```

## Configuration

### Option 1: scrape from a "headlines" or press page

Edit `HEADLINES_URL` in `process_articles.py`:

```python
HEADLINES_URL = "https://yoursite.example/press"
```

The script scrapes this page for article links, then processes each.

### Option 2: hand-curate the URL list

Drop a list of URLs directly into `process_articles.py`, or edit the
dummy `STILL_FAILED` / `FAILED_ARTICLES` lists in `retry_archive.py` and
`retry_failed.py` to point at your own articles.

## Standalone use (Path B)

```bash
cd press-ingest
python3 process_articles.py       # scrape + screenshot
python3 retry_failed.py           # retry the ones that failed (paywalls, JS)
python3 retry_archive.py          # last-resort: Wayback Machine fallback
```

Output:
- `press-html/{year}-{outlet}.html` — cleaned article HTML
- `press-screenshots/{year}-{outlet}-screenshot.png` — full-page PNG

## Vault-aware use (Path A)

```bash
python3 ingest_to_vault.py
```

Reads every cleaned HTML file from `press-html/`, converts to markdown,
adds YAML frontmatter (outlet, year, tags), and writes to
`02_SOURCES/Articles/{year}/` in your vault.

From Claude Code in your vault:

> *"Scrape the press list on my site, retry failed ones, and import
> everything into the vault as proper source notes."*

Claude will run all four scripts in sequence.

## Dummy data

`retry_archive.py` and `retry_failed.py` ship with 3 placeholder URLs
each pointing at `.example` domains. They will fail (which is the
point — it exercises the retry/Wayback path so you can see the flow).
Replace with your own URLs before a real run.
