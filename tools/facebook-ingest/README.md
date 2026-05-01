# facebook-ingest

Takes a Facebook HTML data export and produces:

1. Obsidian-style markdown notes for every DM thread and post
2. A ranked contact list based on message frequency
3. An Excel spreadsheet of your top connections

## Get your export

Facebook → **Settings & Privacy → Settings → Your Information → Download
Your Information**. Pick **HTML** (not JSON — the parser expects HTML).
At minimum include Messages, Posts, Friends, and Profile. Wait for the
download email (can take hours or days).

Unzip into `your_fb_archive/`. See
[`your_fb_archive/README.md`](your_fb_archive/README.md) for the expected
folder structure.

## Configuration

Before running, edit the top of `fb_to_obsidian.py`:

```python
ARCHIVE_DIR = Path(__file__).parent / "your_fb_archive"
OWNER_NAME = "Your Handle"    # your old FB display name
```

Then edit `analyze_contacts.py`:

```python
OWNER = "Your Handle"
```

## Standalone use (Path B)

```bash
cd facebook-ingest
python3 fb_to_obsidian.py         # convert messages + posts to markdown
python3 analyze_contacts.py       # rank contacts by message frequency
python3 build_spreadsheet.py      # top-N Excel file (edit dummy contacts first!)
```

Outputs:
- `_outputs/Messages/*.md` — one file per DM thread
- `_outputs/Posts/*.md` — your posts as notes
- `_outputs/People/*.md` — one file per frequent contact
- `_outputs/Key_Contacts_Social_Profiles.xlsx` — the spreadsheet

## Vault-aware use (Path A)

There's no dedicated `vault_integrate.py` here — `fb_to_obsidian.py` IS
the vault writer. Point its output directly at your vault by editing the
output paths, or from Claude Code:

> *"Run facebook-ingest on `your_fb_archive/`, write message threads to
> `02_SOURCES/Facebook/Messages/`, posts to `02_SOURCES/Facebook/Posts/`,
> and merge contact records into `04_CANON/Shared/People/` where they
> overlap with existing entries."*

The `build_spreadsheet.py` file ships with **dummy contact data** — the
intent is you replace the `contacts = [...]` list with output from
`analyze_contacts.py` once it's run against your real archive.
