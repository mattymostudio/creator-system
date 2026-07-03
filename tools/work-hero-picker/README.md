# work-hero-picker

A small two-script tool for picking the canonical "hero image" of every work
in your archive. Useful when you have many folders, each holding several
photos of the same piece (front, back, raw camera shot, edited export, install
photo, etc.) and you want to choose **one** standardized image per work — for
a website, sales sheet, catalog, or any display surface.

## How it works

1. **`build_picker.py`** scans your archive and generates a single self-contained
   HTML page. Each work is shown as a card with all its candidate images as
   clickable thumbnails.
2. You serve the page locally with `python3 -m http.server`, click through
   choosing one image per work (or "skip"). Selections persist in browser
   localStorage as you go.
3. When done, click **Export selections** in the page — it downloads
   `hero-selections.json`.
4. **`apply_selections.py`** reads that JSON and adds a `_hero/<filename>`
   subfolder inside each chosen work, with a symlink to your pick.

Symlinks only — your originals are never moved.

## Usage

### 1. Generate the picker

If your archive is laid out as `<archive>/<work>/<images>`:

```bash
python3 build_picker.py --works-root path/to/archive
```

If it has a deeper structure like `<archive>/<category>/<work>/<images>` and
you want category headers in the picker:

```bash
python3 build_picker.py \
  --works-glob "path/to/archive/*/*" \
  --group-by-parent \
  --out path/to/archive/hero-picker.html
```

The HTML is written next to your archive root by default.

### 2. Serve and pick

```bash
cd path/to/archive
python3 -m http.server 8765
# open http://localhost:8765/hero-picker.html
```

Click an image to mark it as the hero for that work. Click again to deselect.
Click "skip" if no image works. Selections save automatically.

### 3. Apply

When you're done, click **Export selections** at the top of the page. A file
called `hero-selections.json` downloads to your default Downloads folder. Then:

```bash
python3 apply_selections.py ~/Downloads/hero-selections.json \
  --web-root path/to/archive
```

`--web-root` should be the folder you served via `http.server` — image paths
in the JSON are relative to that.

A `_hero/<chosen-filename>` symlink appears inside every work where you made a
pick. Skipped works are left untouched.

## What you get

For each work with a chosen hero:

```
path/to/archive/<work>/
  _hero/
    chosen-image.jpg     ← symlink to the original
  <all the other files>
```

Downstream tools (a static site builder, a catalog generator, an export script)
can rely on `_hero/` having exactly one image and use it as the canonical
display asset.

## Auto-ranking

Each candidate image gets a heuristic score based on its filename, extension,
and file size. Higher-scoring images appear first in the picker so the most
likely hero is at the top of each work's grid:

| Signal | Score |
|---|---|
| Filename contains the work title (slugified) | +5 |
| Filename contains "front" | +3 |
| Lowercase descriptive name (not `IMG_NNNN`) | +2 |
| `.jpg` / `.png` extension | +2 |
| Long descriptive base name (>12 chars) | +2 |
| File size > 1MB (capped at +4) | +1 per MB |
| Filename starts with `IMG_`, `OS6A`, `DSC` | -3 |
| Filename starts with "Screen Shot" | -5 |
| Filename contains "back" | -2 |
| `.heic`, `.gif`, `.tif` | -1 (browsers don't render well) |

The score is just a sort hint — your eye is the source of truth.

## Notes

- HEIC files appear in the picker as placeholders (browsers can't render them).
  You can still pick them; the JSON records the filename either way.
- If you re-run `apply_selections.py` after changing picks, existing `_hero/`
  contents are replaced.
- `build_picker.py` skips folders prefixed with `_` (treats them as meta /
  internal — e.g. `_meta`, `_hero`, `_tosort`).
- Selections persist in browser localStorage. If you switch browsers or clear
  data, you'll start over (or re-import a saved JSON manually).

## Why a local web server (not `file://`)?

Browsers block `file://` → `file://` image loading for security. Running
`python3 -m http.server` for the duration of the picking session is the
simplest workaround — no install, ships with Python.
