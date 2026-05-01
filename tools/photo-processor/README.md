# Artist Archive Photo Processor

Most creative people take a lot of photos. Tens of thousands a year.
Screenshots of things worth remembering, reference images,
documentation of work in progress, receipts, maps, conversations,
art, memes, whatever. The iPhone becomes an external hard drive for
your brain.

The problem is that dumping 18,000 photos off an iPhone gives you a
folder of `IMG_4392.HEIC` files and nothing else. No context. No
categories. No way to find anything.

That's what this tool is for.

## What it does

This is an eight-stage pipeline that takes a raw iPhone photo dump and turns it into an organized, searchable, categorized archive. There's also a lightweight quick-sort mode for fast type+month organization without AI dependencies. Each stage does one thing well:

1. **Organize** -- Sort everything by type (photo, screenshot, video, saved image) and month. Detects screenshots by matching against every iPhone screen resolution since the iPhone X.

2. **Detect Faces** -- Scan photos for human faces and link them into a People directory. Uses HOG-based face detection, not cloud APIs. Everything stays local.

3. **Extract Screenshots** -- OCR every screenshot using Tesseract, then classify the content into categories (messages, social media, receipts, maps, articles, etc.) based on what the text actually says.

4. **Event Clustering** -- Group photos into events by time proximity. If there's a two-hour gap between shots, that's a new event. Pulls GPS from EXIF when available.

5. **NSFW Scan** -- Flag sensitive content using NudeNet. Sorts into HIGH and MODERATE severity tiers. Because when you're processing 18,000 photos you need to know what's in there before you start sharing folders.

6. **Report Generation** -- Generate detailed markdown reports with monthly breakdowns, category distributions, and content analysis. The detailed classifier handles 30+ categories -- it knows the difference between an Instagram post and an Instagram DM, between a Google search and a stock chart.

7. **Detailed Classification** -- Fine-grained screenshot categorization across 30+ content types using weighted keyword matching on OCR text.

8. **Knowledge Base** -- Build an Obsidian-compatible vault from the processed archive for searchable cross-referencing.

There's also an entity extractor that pulls structured data (phone numbers, emails, URLs, social handles, addresses, dates, prices) out of the OCR text, and a file canonicalizer for standardizing filenames.

## The philosophy

If you believe the archive outlasts the work — that documenting and
organizing your creative life is as important as the work itself —
then an unsorted folder of 18,000 `IMG_*.HEIC` files is unacceptable.

This tool exists to process years of iPhone dumps into something you
can search, reference, and build on. Every screenshot of a
conversation, every photo of an installation in progress, every
receipt from a road trip — it all has value if you can find it.

## Usage

### Quick Sort (fast, no dependencies)

For a fast type-and-month sort with no AI/OCR overhead -- just drop files in `new/` and run:

```bash
python3 scripts/quick_sort.py new --move
```

This classifies files into Photos, Screenshots, Videos, Saved_Images, and Other, organized by month. Output goes to `Organized/`. Uses EXIF data and PNG header resolution checks to detect screenshots -- no PIL or ML models needed, just `exifread`.

### Full Pipeline

```bash
./process.sh /path/to/iphone/dump
```

Runs all eight stages in sequence. Output lands in an `Organized/` directory next to your source folder.

To run individual stages:

```bash
python3 scripts/organize.py /path/to/dump
python3 scripts/detect_faces.py --organized-dir Organized
python3 scripts/extract_screenshots.py --organized-dir Organized
python3 scripts/event_cluster.py --organized-dir Organized
python3 scripts/nsfw_scan.py --organized-dir Organized
python3 scripts/screenshot_report.py --organized-dir Organized
python3 scripts/classify_detailed.py --organized-dir Organized
```

### Standalone vs. vault-aware

The steps above are the **standalone** path — output lands in a local
`Organized/` folder. Useful on its own.

If you've set up the sibling Obsidian vault, run the vault backfill as
the final step:

```bash
python3 scripts/backfill_vault.py --organized-dir Organized
```

This reads the processed archive and writes event notes into
`02_SOURCES/Photos/{year}/` in your vault, links faces to the
`04_CANON/Shared/People/` directory, and generates a cross-linked
summary for each detected event. From Claude Code in your vault:

> *"Run the photo-processor on `~/Pictures/iPhone-Export/`, then
> backfill the vault."*

## Dependencies

```bash
pip install -r requirements.txt
```

You'll also need [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr
```

The face recognition library requires `dlib`, which can be finicky to install. On macOS with Homebrew:

```bash
brew install cmake
pip install dlib
pip install face-recognition
```

## How it works under the hood

- All stages use symlinks for secondary organization (People, Events, Flagged). Your originals stay in one place.
- HEIC/HEIF support throughout -- no need to convert iPhone photos first.
- Screenshot classification uses weighted keyword matching, not ML models. It's fast, deterministic, and easy to extend.
- Reports output in both Markdown and JSON so you can read them or pipe them into other tools.
- Everything runs locally. No cloud APIs, no uploads, no accounts.

## What this isn't

This isn't a photo editor, a gallery app, or a backup service. It's a processing pipeline for people who think of their photo library as a dataset, not a scrapbook.
