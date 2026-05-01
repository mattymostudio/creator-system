# Put your Facebook archive here

This folder is where you unzip your Facebook data export.

## How to get your archive

1. Go to **Settings & Privacy → Settings → Your Information → Download Your Information**
2. Choose **HTML** format (not JSON — the parser expects HTML)
3. Select the date range and data types (at minimum: Messages, Posts, Friends, Profile)
4. Wait for the download email (can take hours to days)
5. Unzip the archive into this folder

## Expected structure (after unzip)

```
your_fb_archive/
├── messages/
│   └── inbox/
│       ├── firstname_lastname_xxx/
│       │   └── message_1.html
│       └── ...
├── posts/
│   └── your_posts_1.html
├── friends_and_followers/
├── profile_information/
└── ...
```

The scripts read from `messages/inbox/` and `posts/`.

## Running the tool

```bash
python3 fb_to_obsidian.py     # convert to Obsidian markdown
python3 analyze_contacts.py   # rank contacts by message frequency
python3 build_spreadsheet.py  # build the top-N contacts Excel file
```

## If you're just demoing

A tiny demo structure can be invented: create
`your_fb_archive/messages/inbox/sample_contact/message_1.html` with
any valid FB-like HTML and the parser will pick it up. Easier, though,
is to run the tool once on your own archive to see how it works.
