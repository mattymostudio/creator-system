# takeout-processor

Extracts contacts, timelines, and relationship graphs from a Google
Takeout archive. Biggest tool in the kit — budget 30+ minutes for a
first run on a real archive.

## Get your Takeout

[takeout.google.com](https://takeout.google.com/) → select Mail,
Contacts, Calendar → `.zip` format. Drop the zips in `00_raw_takeouts/`.

## Pipeline stages

```
00_raw_takeouts/              raw .zip archives (you put these here)
    ↓ unzip + mbox extract
01_contact_bundles/           one JSON per unique contact email
    ↓ LLM enrichment (optional, uses Claude API)
02_enriched_bundles/          same contacts + relationship summaries
    ↓ aggregate
03_master_csvs/               unified contacts, timeline, relationship graph
```

## Standalone use (Path B)

Run stages in `05_scripts/` one at a time, inspecting output between each.
Most scripts have `--dry-run` where it matters.

```bash
cd takeout-processor
python3 05_scripts/mbox_extract_bodies.py     # extract from mbox
python3 05_scripts/build_master_csv.py        # aggregate
python3 05_scripts/build_timeline.py          # interaction timeline
python3 05_scripts/build_relationship_graph.py  # who-knows-whom
```

Outputs are CSVs and JSONs under `01_*` through `03_*`. Open them in
any spreadsheet tool.

## Vault-aware use (Path A)

```bash
python3 05_scripts/vault_integrate.py
```

This writes one markdown note per contact into
`04_CANON/Shared/People/` in your vault, with YAML frontmatter containing
the email-derived relationship summary, first/last contact dates, and
cross-links to any mentioned projects.

From Claude Code in your vault:

> *"Run takeout-processor end-to-end on my latest Takeout. Skip the LLM
> enrichment — I just want the master CSV and the vault contact notes."*

## Configuration

Edit the "your own email addresses" list at the top of each aggregation
script (e.g., `build_timeline.py`, `build_mm_contacts.py`,
`build_relationship_graph.py`, `mbox_extract_bodies.py`). These are the
addresses the scripts treat as **you**, so they get excluded from the
contact list. Replace the placeholder `you@yourdomain.example` entries
with your real addresses.

The LLM enrichment step (`llm_enrich.py`) edits the system prompt to
describe who you are and what projects you work on. Edit that prompt to
match your own context before running — it's the only script that
sends data to an external API.
