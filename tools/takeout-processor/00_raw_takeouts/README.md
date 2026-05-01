# Drop raw Google Takeout exports here

## How to get your Takeout

1. Go to [takeout.google.com](https://takeout.google.com/)
2. Select data you want — at minimum: **Mail**, **Contacts**, **Calendar**
3. Choose **.zip** or **.tgz** format
4. Wait for the email (can take hours for large accounts)
5. Download the archives and drop them here

## Expected layout

```
00_raw_takeouts/
├── takeout-20260101T120000Z-001.zip
├── takeout-20260101T120000Z-002.zip
└── ...
```

The pipeline scripts unzip these into working directories and scan the
`.mbox` file inside for contact extraction.

## What the pipeline does (summary)

```
00_raw_takeouts/          ← raw zips (here)
    ↓ unzip + extract
01_contact_bundles/       ← one JSON per contact (email address)
    ↓ LLM enrichment
02_enriched_bundles/      ← same contacts + relationship metadata
    ↓ aggregate
03_master_csvs/           ← unified contact CSV, timeline, relationship graph
    ↓
vault_integrate.py        ← writes People notes to your Obsidian vault
```

Scripts live in `05_scripts/`. They're designed to run one stage at a time
so you can inspect output between each step.
